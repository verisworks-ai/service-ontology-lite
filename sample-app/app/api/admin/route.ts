export async function POST(request: Request) {
  const authorization = request.headers.get('authorization')
  if (!authorization) return Response.json({ error: 'missing auth' }, { status: 401 })
  return Response.json({ ok: true, notified: Boolean(process.env.DISCORD_WEBHOOK_URL) })
}
