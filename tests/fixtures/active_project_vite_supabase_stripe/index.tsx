import { createClient } from "@supabase/supabase-js";
import { BrowserRouter } from "react-router-dom";

export const supabase = createClient("https://example.supabase.co", "anon-key");

export function App() {
  return <BrowserRouter />;
}
