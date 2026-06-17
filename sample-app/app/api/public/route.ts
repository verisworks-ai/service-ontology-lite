export async function GET() {
  return Response.json({ ok: true, provider: process.env.SUPABASE_URL })
}
