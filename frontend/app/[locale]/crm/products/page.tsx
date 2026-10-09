"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useProducts, useCreateProduct, useUpdateProduct, useDeleteProduct,
  useSegments, useCreateSegment, useDeleteSegment,
  useTagAnalytics, useIndustrySegments, useSourcePerformance,
  type Product,
} from "@/hooks/useProducts";
import {
  Package, Plus, Edit, Trash2, MoreHorizontal, Tag,
  Users, BarChart3, CheckCircle2, Loader2, Filter,
} from "lucide-react";

function formatEUR(n: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n);
}

// ── Product Row ───────────────────────────────────────────────
function ProductRow({ product, onEdit, onDelete }: {
  product: Product;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4 hover:bg-muted/30 transition-colors">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <Package className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-medium text-sm truncate">{product.name}</p>
          <Badge variant={product.isActive ? "default" : "secondary"} className="text-[9px]">
            {product.isActive ? "Attivo" : "Inattivo"}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground truncate">{product.description}</p>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="outline" className="text-[9px]">{product.category}</Badge>
          <Badge variant="outline" className="text-[9px]">{product.billingModel}</Badge>
          {product.sku && <span className="text-[10px] text-muted-foreground">SKU: {product.sku}</span>}
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className="font-semibold">{formatEUR(product.price)}</p>
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8" />}>
          <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={onEdit}>
            <Edit className="mr-2 h-4 w-4" />
            Modifica
          </DropdownMenuItem>
          {!confirm ? (
            <DropdownMenuItem variant="destructive" onClick={() => setConfirm(true)}>
              <Trash2 className="mr-2 h-4 w-4" />
              Elimina
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem variant="destructive" onClick={() => { onDelete(); setConfirm(false); }}>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Conferma
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function ProductsPage() {
  const [tab, setTab] = useState<"products" | "segments" | "analytics">("products");

  // Products
  const { data: products, isLoading: prodLoading } = useProducts();
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();
  const deleteProduct = useDeleteProduct();

  // Segments
  const { data: segments, isLoading: segLoading } = useSegments();
  const createSegment = useCreateSegment();
  const deleteSegment = useDeleteSegment();

  // Analytics
  const { data: tagData, isLoading: tagLoading } = useTagAnalytics();
  const { data: industryData, isLoading: indLoading } = useIndustrySegments();
  const { data: sourceData, isLoading: srcLoading } = useSourcePerformance();

  // Dialog state
  const [productDialog, setProductDialog] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [productForm, setProductForm] = useState({ name: "", description: "", price: 0, category: "software", billingModel: "one-time", sku: "" });

  const [segmentDialog, setSegmentDialog] = useState(false);
  const [segmentForm, setSegmentForm] = useState({ name: "", description: "", status: "", source: "", industry: "", minScore: "" });

  function openCreateProduct() {
    setEditingProduct(null);
    setProductForm({ name: "", description: "", price: 0, category: "software", billingModel: "one-time", sku: "" });
    setProductDialog(true);
  }

  function openEditProduct(p: Product) {
    setEditingProduct(p);
    setProductForm({ name: p.name, description: p.description, price: p.price, category: p.category, billingModel: p.billingModel, sku: p.sku });
    setProductDialog(true);
  }

  async function handleSaveProduct() {
    const data = { ...productForm, price: Number(productForm.price) };
    if (editingProduct) {
      await updateProduct.mutateAsync({ id: editingProduct.id, data });
    } else {
      await createProduct.mutateAsync(data);
    }
    setProductDialog(false);
  }

  async function handleSaveSegment() {
    const rules: Record<string, unknown> = {};
    if (segmentForm.status) rules.status = segmentForm.status;
    if (segmentForm.source) rules.source = segmentForm.source;
    if (segmentForm.industry) rules.industry = segmentForm.industry;
    if (segmentForm.minScore) rules.minScore = Number(segmentForm.minScore);
    await createSegment.mutateAsync({ name: segmentForm.name, description: segmentForm.description, rules });
    setSegmentDialog(false);
    setSegmentForm({ name: "", description: "", status: "", source: "", industry: "", minScore: "" });
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Catalogo & Segmentazione</h1>
          <p className="text-sm text-muted-foreground">
            Gestisci prodotti, segmenti clienti e analisi di conversione
          </p>
        </div>
        <Tabs value={tab} onValueChange={(v) => v && setTab(v as typeof tab)}>
          <TabsList>
            <TabsTrigger value="products">Prodotti</TabsTrigger>
            <TabsTrigger value="segments">Segmenti</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* ═══ Products Tab ═══ */}
      {tab === "products" && (
        <>
          <div className="flex justify-end">
            <Button size="sm" onClick={openCreateProduct}>
              <Plus className="h-3.5 w-3.5 mr-1" />
              Nuovo Prodotto
            </Button>
          </div>
          {prodLoading ? (
            <div className="space-y-3">{[1, 2, 3].map(i => <Skeleton key={i} className="h-20 w-full rounded-lg" />)}</div>
          ) : !products?.length ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 gap-3">
                <Package className="h-10 w-10 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">Nessun prodotto nel catalogo</p>
                <Button variant="outline" size="sm" onClick={openCreateProduct}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Crea Primo Prodotto
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {products.map((p) => (
                <ProductRow
                  key={p.id}
                  product={p}
                  onEdit={() => openEditProduct(p)}
                  onDelete={() => deleteProduct.mutate(p.id)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* ═══ Segments Tab ═══ */}
      {tab === "segments" && (
        <>
          <div className="flex justify-end">
            <Button size="sm" onClick={() => setSegmentDialog(true)}>
              <Plus className="h-3.5 w-3.5 mr-1" />
              Nuovo Segmento
            </Button>
          </div>
          {segLoading ? (
            <div className="space-y-3">{[1, 2].map(i => <Skeleton key={i} className="h-24 w-full rounded-lg" />)}</div>
          ) : !segments?.length ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 gap-3">
                <Filter className="h-10 w-10 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">Nessun segmento creato</p>
                <Button variant="outline" size="sm" onClick={() => setSegmentDialog(true)}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Crea Primo Segmento
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {segments.map((seg) => (
                <Card key={seg.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm">{seg.name}</h3>
                          {seg.isGlobal && <Badge variant="secondary" className="text-[8px]">Globale</Badge>}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{seg.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-[9px]">
                            <Users className="h-2.5 w-2.5 mr-1" />
                            {seg.matchCount} lead
                          </Badge>
                          {Object.entries(seg.rules).map(([k, v]) => (
                            <Badge key={k} variant="secondary" className="text-[9px]">
                              {k}: {String(v)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive"
                        onClick={() => deleteSegment.mutate(seg.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* ═══ Analytics Tab ═══ */}
      {tab === "analytics" && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Tag Analytics */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top Tag</CardTitle>
              <CardDescription>Tag più usati sui lead</CardDescription>
            </CardHeader>
            <CardContent>
              {tagLoading ? <Skeleton className="h-48 w-full" /> : !tagData?.length ? (
                <p className="text-sm text-muted-foreground text-center py-8">Nessun tag</p>
              ) : (
                <div className="space-y-2">
                  {tagData.slice(0, 10).map((t) => (
                    <div key={t.tag} className="flex items-center gap-2">
                      <Tag className="h-3 w-3 text-muted-foreground shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{t.tag}</span>
                          <span className="text-xs text-muted-foreground">{t.count} lead</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-muted/50 mt-1">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(t.count * 5, 100)}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Industry Segments */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Per Settore</CardTitle>
              <CardDescription>Distribuzione lead per industria</CardDescription>
            </CardHeader>
            <CardContent>
              {indLoading ? <Skeleton className="h-48 w-full" /> : !industryData?.length ? (
                <p className="text-sm text-muted-foreground text-center py-8">Nessun dato</p>
              ) : (
                <div className="space-y-3">
                  {industryData.slice(0, 8).map((ind) => (
                    <div key={ind.industry} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm">{ind.industry}</p>
                        <p className="text-[10px] text-muted-foreground">Score medio: {ind.avgScore}</p>
                      </div>
                      <Badge variant="secondary" className="text-xs">{ind.total}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Source Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Performance Fonti</CardTitle>
              <CardDescription>Tasso di conversione per fonte</CardDescription>
            </CardHeader>
            <CardContent>
              {srcLoading ? <Skeleton className="h-48 w-full" /> : !sourceData?.length ? (
                <p className="text-sm text-muted-foreground text-center py-8">Nessun dato</p>
              ) : (
                <div className="space-y-3">
                  {sourceData.slice(0, 8).map((s) => (
                    <div key={s.source} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm">{s.source}</p>
                        <p className="text-[10px] text-muted-foreground">{s.converted}/{s.total} convertiti</p>
                      </div>
                      <Badge variant={s.conversionRate >= 20 ? "default" : "secondary"} className="text-xs">
                        {s.conversionRate}%
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Product Dialog ── */}
      <Dialog open={productDialog} onOpenChange={setProductDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingProduct ? "Modifica Prodotto" : "Nuovo Prodotto"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Nome</Label>
              <Input value={productForm.name} onChange={e => setProductForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <Label>Descrizione</Label>
              <Textarea value={productForm.description} onChange={e => setProductForm(f => ({ ...f, description: e.target.value }))} rows={2} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Prezzo (€)</Label>
                <Input type="number" value={productForm.price} onChange={e => setProductForm(f => ({ ...f, price: Number(e.target.value) }))} />
              </div>
              <div className="space-y-1">
                <Label>SKU</Label>
                <Input value={productForm.sku} onChange={e => setProductForm(f => ({ ...f, sku: e.target.value }))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Categoria</Label>
                <select value={productForm.category} onChange={e => setProductForm(f => ({ ...f, category: e.target.value }))}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="software">Software</option>
                  <option value="service">Servizio</option>
                  <option value="consulting">Consulenza</option>
                  <option value="other">Altro</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label>Fatturazione</Label>
                <select value={productForm.billingModel} onChange={e => setProductForm(f => ({ ...f, billingModel: e.target.value }))}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="one-time">Una tantum</option>
                  <option value="monthly">Mensile</option>
                  <option value="yearly">Annuale</option>
                </select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProductDialog(false)}>Annulla</Button>
            <Button onClick={handleSaveProduct} disabled={!productForm.name || createProduct.isPending || updateProduct.isPending}>
              {(createProduct.isPending || updateProduct.isPending) && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Salva
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Segment Dialog ── */}
      <Dialog open={segmentDialog} onOpenChange={setSegmentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuovo Segmento</DialogTitle>
            <DialogDescription>Definisci regole per filtrare i lead dinamicamente</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Nome</Label>
              <Input value={segmentForm.name} onChange={e => setSegmentForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <Label>Descrizione</Label>
              <Input value={segmentForm.description} onChange={e => setSegmentForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Status</Label>
                <select value={segmentForm.status} onChange={e => setSegmentForm(f => ({ ...f, status: e.target.value }))}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="">Qualsiasi</option>
                  <option value="new">Nuovo</option>
                  <option value="contacted">Contattato</option>
                  <option value="qualified">Qualificato</option>
                  <option value="proposal">Proposta</option>
                  <option value="won">Vinto</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label>Fonte</Label>
                <select value={segmentForm.source} onChange={e => setSegmentForm(f => ({ ...f, source: e.target.value }))}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="">Qualsiasi</option>
                  <option value="playbook">Playbook</option>
                  <option value="contact">Contact Form</option>
                  <option value="booking">Booking</option>
                  <option value="excel_import">Excel Import</option>
                  <option value="referral">Referral</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Settore</Label>
                <Input value={segmentForm.industry} onChange={e => setSegmentForm(f => ({ ...f, industry: e.target.value }))} placeholder="es. Legal" />
              </div>
              <div className="space-y-1">
                <Label>Score minimo</Label>
                <Input type="number" min="0" max="100" value={segmentForm.minScore} onChange={e => setSegmentForm(f => ({ ...f, minScore: e.target.value }))} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSegmentDialog(false)}>Annulla</Button>
            <Button onClick={handleSaveSegment} disabled={!segmentForm.name || createSegment.isPending}>
              {createSegment.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Crea
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}