# ADR-002: MongoDB via Docker per sviluppo locale

**Data**: 2026-05-16
**Stato**: Accettato
**Deciders**: Team AiChain

---

## Contesto

Il progetto usa MongoDB come database principale (driver `motor` async). In locale `mongod` non è installato nativamente. Per lo sviluppo locale è necessaria un'istanza MongoDB raggiungibile su `localhost:27017`.

---

## Decisione

**Usare Docker per eseguire MongoDB in locale**, senza installare `mongod` sul sistema host.

```bash
docker run -d \
  --name mongodb-crm \
  -p 27017:27017 \
  -e MONGO_INITDB_DATABASE=crm-aichain-db \
  mongo:7

docker update --restart unless-stopped mongodb-crm
```

Connessione: `mongodb://localhost:27017` — Database: `crm-aichain-db`

---

## Motivo

- Docker è già disponibile sul sistema di sviluppo (verificato: Docker 29.3.0)
- Evita di installare MongoDB nativamente (dipendenze di sistema, versioni conflittuali)
- Il container si avvia automaticamente al boot del sistema (`--restart unless-stopped`)
- Isolamento: il container può essere rimosso e ricreato senza toccare il sistema host

---

## Conseguenze

### Positive
- Ambiente ripetibile e pulito
- Nessuna dipendenza di sistema per MongoDB
- Facile reset del DB: `docker rm -f mongodb-crm` + ricreazione

### Negative / Attenzioni

1. **Il container deve essere avviato prima del backend.** Se Docker non è in esecuzione o il container è fermo, il backend restituisce 403 su tutti gli endpoint autenticati (perché non riesce a verificare l'utente in MongoDB).

2. **Dopo la creazione di un nuovo container, il DB è vuoto.** La collection `users` deve essere popolata manualmente o tramite seed script prima di poter usare l'applicazione. Senza utenti nel DB, `get_current_user` (deps.py) ritorna 403 per qualsiasi JWT valido.

3. **I dati non persistono se il container viene rimosso** con `docker rm`. Per persistenza tra ricreazioni, usare un volume Docker:
   ```bash
   docker run -d --name mongodb-crm -p 27017:27017 \
     -v mongodb-crm-data:/data/db mongo:7
   ```

---

## Procedura di recovery

### Il backend restituisce 403 su tutti gli endpoint

```bash
# Step 1: verificare MongoDB
docker ps | grep mongodb-crm

# Step 2: avviare se fermo
docker start mongodb-crm

# Step 3: verificare collection users
docker exec -it mongodb-crm mongosh crm-aichain-db \
  --eval "db.users.countDocuments()"

# Step 4: se count == 0, inserire utenti di sviluppo
docker exec -it mongodb-crm mongosh crm-aichain-db --eval "
db.users.insertMany([
  { uid: 'eHFeSPGP8cWxWHFcM5In4KVYQQ42', email: 'fred@it.it', role: 'admin', isActive: true, createdAt: new Date() },
  { uid: 'fFW6zJBJxCYQ77y0vXskwuFQEIH3', email: 'admin@aichain.it', role: 'admin', isActive: true, createdAt: new Date() },
  { uid: 'JY9qlgBlfWMmtSLo4n2bjte6q8Z2', email: 'marketing@aichainsolutions.net', role: 'sales', isActive: true, createdAt: new Date() }
])
"

# Step 5: riavviare il backend uvicorn
```

---

## Note per LLM

- Se l'utente segnala 403 su tutti gli endpoint → **prima cosa da verificare: MongoDB Docker**.
- Non confondere con errori di token Firebase: quelli producono 401, non 403.
- 403 "Utente non registrato nel CRM" = utente autenticato in Firebase ma assente in MongoDB `users`.
- Il flusso auth è: Firebase JWT verificato → `uid` cercato in MongoDB `users` → se non trovato → 403.
