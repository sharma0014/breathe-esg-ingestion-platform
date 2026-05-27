import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { clearTokens, ensureDemoOrg, getMyOrgs, login } from './api'

type AuthState = {
  isAuthenticated: boolean
  orgSlug: string | null
  setOrgSlug: (slug: string) => void
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('access_token'),
  )
  const [orgSlug, setOrgSlugState] = useState<string | null>(
    localStorage.getItem('org_slug'),
  )

  function setOrgSlug(slug: string) {
    localStorage.setItem('org_slug', slug)
    setOrgSlugState(slug)
  }

  async function doLogin(username: string, password: string) {
    await login(username, password)
    setIsAuthenticated(true)

    // pick an org (or create a demo one in dev)
    try {
      const orgs = await getMyOrgs()
      if (orgs.length > 0) {
        setOrgSlug(orgs[0].org.slug)
        return
      }
      await ensureDemoOrg()
      const orgs2 = await getMyOrgs()
      if (orgs2.length > 0) setOrgSlug(orgs2[0].org.slug)
    } catch {
      // leave org unset; pages will show an error
    }
  }

  function logout() {
    clearTokens()
    localStorage.removeItem('org_slug')
    setIsAuthenticated(false)
    setOrgSlugState(null)
  }

  // if tokens exist but org missing, try to load
  useEffect(() => {
    if (!isAuthenticated || orgSlug) return
    ;(async () => {
      try {
        const orgs = await getMyOrgs()
        if (orgs.length > 0) setOrgSlug(orgs[0].org.slug)
      } catch {
        // ignore
      }
    })()
  }, [isAuthenticated, orgSlug])

  const value = useMemo<AuthState>(
    () => ({ isAuthenticated, orgSlug, setOrgSlug, login: doLogin, logout }),
    [isAuthenticated, orgSlug],
  )

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth() {
  const v = useContext(Ctx)
  if (!v) throw new Error('AuthProvider missing')
  return v
}
