import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.lead_service import LeadService
from app.schemas.lead import LeadCreate, LeadUpdate, LeadStageUpdate

@pytest.mark.asyncio
async def test_find_by_email_found():
    with patch("app.services.lead_service.db") as mock_db:
        mock_stream = AsyncMock()
        
        # Simulate returning a document from stream
        mock_snap = MagicMock()
        mock_snap.id = "123"
        mock_snap.to_dict.return_value = {"email": "test@test.com", "deletedAt": None}
        
        # Need to implement async generator for stream()
        async def mock_async_gen():
            yield mock_snap
            
        mock_db.collection.return_value.where.return_value.where.return_value.limit.return_value.stream = mock_async_gen
        
        service = LeadService()
        result = await service.find_by_email("test@test.com")
        
        assert result is not None
        assert result["id"] == "123"

@pytest.mark.asyncio
async def test_create_lead():
    data = LeadCreate(email="new@test.com")
    
    with patch("app.services.lead_service.create_document", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"id": "lead_123", "email": "new@test.com"}
        with patch("app.services.lead_service.append_activity", new_callable=AsyncMock) as mock_append:
            
            service = LeadService()
            result = await service.create_lead(data, "user_1")
            
            assert result["id"] == "lead_123"
            mock_create.assert_called_once()
            mock_append.assert_called_once()

@pytest.mark.asyncio
async def test_create_or_update_from_form_create():
    with patch.object(LeadService, "find_by_email", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        
        with patch("app.services.lead_service.create_document", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": "lead_new"}
            with patch("app.services.lead_service.append_activity", new_callable=AsyncMock) as mock_append:
                
                service = LeadService()
                result = await service.create_or_update_from_form("form@test.com", {"firstName": "Test"}, "contact", "direct", "127.0.0.1", "ua")
                
                assert result["id"] == "lead_new"
                mock_create.assert_called_once()
                mock_append.assert_called_once()


@pytest.mark.asyncio
async def test_import_csv():
    csv_content = """phone_number,first_name,last_name,company_name,city,email
+39 0461 211411,Antonio,Martinelli,OPERA SOCIETA' TRA PROFESSIONISTI S.R.L.,Trento,pipo1@gmail.com
+39 0574 40291,Ascanio,Marradi,CON.SE.A. PRATO - CONFESERCENTI SERVIZI AMMINISTRATIVI E FINAN- ZIARI S.R.L.,Prato,pipo2@gmail.com
"""
    
    with patch.object(LeadService, "find_by_email", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = None
        
        with patch.object(LeadService, "create_lead", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                {"id": "lead_1"},
                {"id": "lead_2"}
            ]
            
            service = LeadService()
            results = await service.import_csv(csv_content, "user_1")
            
            assert results["total"] == 2
            assert results["imported"] == 2
            assert results["skipped"] == 0
            assert len(results["errors"]) == 0
            assert mock_find.call_count == 2
            assert mock_create.call_count == 2
