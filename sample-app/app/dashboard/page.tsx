import { getServerSession } from 'next-auth'

export default async function DashboardPage() {
  const session = await getServerSession()
  return <main>Private dashboard {session?.user?.email}</main>
}
