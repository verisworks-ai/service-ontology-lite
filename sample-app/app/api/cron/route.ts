export async function GET(request: Request) {
  const authorization = request.headers.get('authorization')
  if (!authorization) return Response.json({ error: 'missing cron token' }, { status: 401 })
  return Response.json({ ok: true })
}
