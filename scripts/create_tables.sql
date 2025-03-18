-- Create podcasts table
CREATE TABLE IF NOT EXISTS public.podcasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  sport TEXT NOT NULL,
  event_id TEXT,
  episode_type TEXT,
  duration INTEGER,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  metadata JSONB,
  script_text TEXT,
  audio_url TEXT,
  script_url TEXT
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.podcasts ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Allow anonymous read access
CREATE POLICY "Allow anonymous read access" 
  ON public.podcasts 
  FOR SELECT 
  USING (true);

-- Allow service role to manage all podcasts
CREATE POLICY "Allow service role full access" 
  ON public.podcasts 
  USING (auth.role() = 'service_role');

-- Create generation_logs table
CREATE TABLE IF NOT EXISTS public.generation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  podcast_id UUID REFERENCES public.podcasts(id) ON DELETE CASCADE,
  agent_name TEXT NOT NULL,
  message TEXT NOT NULL,
  level TEXT DEFAULT 'info',
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.generation_logs ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Allow service role to manage all logs
CREATE POLICY "Allow service role full access" 
  ON public.generation_logs 
  USING (auth.role() = 'service_role');
  
-- Allow anonymous to read logs
CREATE POLICY "Allow anonymous read access" 
  ON public.generation_logs 
  FOR SELECT 
  USING (true);

-- Create health_check table
CREATE TABLE IF NOT EXISTS public.health_check (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  last_checked TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Insert a test record
INSERT INTO public.health_check (name, status)
VALUES ('supabase', 'healthy')
ON CONFLICT DO NOTHING; 