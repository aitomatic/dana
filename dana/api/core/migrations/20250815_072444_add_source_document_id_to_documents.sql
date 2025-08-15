-- Migration: add_source_document_id_to_documents
-- Created: 2025-08-15T07:24:44.489825+00:00

-- Add source_document_id column to documents table for JSON extraction relationships
ALTER TABLE documents ADD COLUMN source_document_id INTEGER REFERENCES documents(id);
