-- Table: podcasts
-- Main table to store information about each podcast
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

-- Table: generation_logs
-- Detailed logs for the podcast generation process
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

-- Table: users
-- Store user information for the web dashboard
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  email TEXT,
  display_name TEXT,
  avatar_url TEXT,
  role TEXT DEFAULT 'user',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Allow users to read their own profiles
CREATE POLICY "Allow users to read own profile"
  ON public.user_profiles
  FOR SELECT
  USING (auth.uid() = id);
  
-- Allow service role full access
CREATE POLICY "Allow service role full access"
  ON public.user_profiles
  USING (auth.role() = 'service_role');

-- Create or replace a function to handle user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, display_name)
  VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'name', NEW.email));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create the trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create storage buckets
-- First check if the storage schema exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'storage') THEN
    -- Create audio bucket
    INSERT INTO storage.buckets (id, name, public)
    VALUES ('audio', 'audio', true)
    ON CONFLICT (id) DO NOTHING;

    -- Create scripts bucket
    INSERT INTO storage.buckets (id, name, public)
    VALUES ('scripts', 'scripts', true)
    ON CONFLICT (id) DO NOTHING;

    -- Create user_uploads bucket
    INSERT INTO storage.buckets (id, name, public)
    VALUES ('user_uploads', 'user_uploads', false)
    ON CONFLICT (id) DO NOTHING;
  END IF;
END $$; 