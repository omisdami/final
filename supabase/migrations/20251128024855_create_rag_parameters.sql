/*
  # RAG Parameter Configuration System
  
  This migration creates the data model for storing and managing RAG (Retrieval-Augmented Generation) parameters.
  
  1. New Tables
    - `rag_parameter_configs`
      - `id` (uuid, primary key)
      - `user_id` (uuid, foreign key to auth.users)
      - `name` (text) - Configuration name
      - `similarity_threshold` (numeric) - Minimum relevance score (0.0-1.0)
      - `top_k` (integer) - Number of top documents to retrieve (1-50)
      - `chunk_size` (integer) - Size of text chunks in tokens (100-2000)
      - `overlap` (integer) - Chunk overlap percentage (0-50)
      - `is_default` (boolean) - Whether this is the user's default configuration
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)
  
  2. Security
    - Enable RLS on `rag_parameter_configs` table
    - Add policies for authenticated users to manage their own configurations
*/

CREATE TABLE IF NOT EXISTS rag_parameter_configs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,
  similarity_threshold numeric NOT NULL DEFAULT 0.6 CHECK (similarity_threshold >= 0 AND similarity_threshold <= 1),
  top_k integer NOT NULL DEFAULT 5 CHECK (top_k >= 1 AND top_k <= 50),
  chunk_size integer NOT NULL DEFAULT 512 CHECK (chunk_size >= 100 AND chunk_size <= 2000),
  overlap integer NOT NULL DEFAULT 15 CHECK (overlap >= 0 AND overlap <= 50),
  is_default boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE rag_parameter_configs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own configurations
CREATE POLICY "Users can view own RAG configurations"
  ON rag_parameter_configs
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own configurations
CREATE POLICY "Users can create own RAG configurations"
  ON rag_parameter_configs
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own configurations
CREATE POLICY "Users can update own RAG configurations"
  ON rag_parameter_configs
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own configurations
CREATE POLICY "Users can delete own RAG configurations"
  ON rag_parameter_configs
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_rag_configs_user_id ON rag_parameter_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_configs_is_default ON rag_parameter_configs(user_id, is_default);
