import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Route, Routes, useNavigate } from 'react-router-dom'
import './App.css'

const API = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

type User = { id: number; name: string; institute_email: string; role: 'student' | 'mentor' | 'admin'; account_status: string }
type Mentor = { id: number; user_id: number; name: string; experience_level: string; roles: string | null; organisations: string | null; guidance_types: string | null; max_mentee_capacity: number }
type MentoringRequest = { id: number; student_id: number; mentor_id: number; personal_message: string; status: string; student?: { name: string; career_goal: string | null; current_situation: string | null; career_question: string | null } }
type Relationship = {
  id: number; student_id: number; mentor_id: number; student_name: string; mentor_name: string; status: string; started_at: string; last_activity_at: string
  student_career_goal?: string | null; student_interests?: string[]; current_question?: string | null; mentor_career_history?: string | null; mentor_expertise?: string[]
}
type Question = { id: number; question_text: string; created_at: string }
type NotificationItem = { id: number; type: string; message: string; is_read: boolean; created_at: string }
type Recommendation = { mentor_id: number; mentor_name: string; match_score: number; match_explanation: string[] }
type AdminUser = { id: number; name: string; role: string; account_status: string }
type Application = { id: number; user_id: number; status: string; roll_number: string | null; graduation_year: number | null }
type Report = { id: number; reporter_id: number; target_user_id: number; category: string; description: string; status: string }
type DashboardData = {
  mentors: Mentor[]
  requests: MentoringRequest[]
  relationships: Relationship[]
  questions: Question[]
  recommendations: Recommendation[]
  notifications: NotificationItem[]
  users: AdminUser[]
  applications: Application[]
  reports: Report[]
  analytics: Record<string, number>
  alerts: { stale_requests: { id: number; mentor_id: number }[]; inactive_relationships: { id: number }[] }
}

async function api<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API}${path}`, { ...init, headers })
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function HomePage() {
  return (
    <main className="page-shell">
      <header className="topbar">
        <div><p className="eyebrow">IITM BS</p><h1>Student Mentoring Platform</h1></div>
        <nav className="nav-actions"><Link to="/login">Login</Link><Link to="/register">Register</Link></nav>
      </header>
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="pill">Career support for IITM BS students</span>
          <h2>Connect students with experienced guides and trusted mentors.</h2>
          <p>Discover mentors, request guidance and keep mentoring activity in one place.</p>
          <div className="cta-row"><Link className="primary-btn" to="/register">Create account</Link><Link className="secondary-btn" to="/login">Sign in</Link></div>
        </div>
        <aside className="stats-card"><div><strong>3</strong><span>Platform roles</span></div><div><strong>1:1</strong><span>Personal mentoring</span></div><div><strong>IITM</strong><span>Institute community</span></div></aside>
      </section>
      <section className="info-grid">
        {[
          ['Students', 'Build a career profile, ask questions and request a mentor.'],
          ['Mentors', 'Apply, share your expertise and guide assigned mentees.'],
          ['Administrators', 'Review applications and reports, and manage accounts.'],
        ].map(([title, text]) => <article key={title} className="feature-card"><h3>{title}</h3><p>{text}</p></article>)}
      </section>
    </main>
  )
}

function AuthPage({ mode, onAuthenticated }: { mode: 'login' | 'register'; onAuthenticated: (token: string) => void }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setBusy(true)
    const data = new FormData(event.currentTarget)
    const payload = mode === 'login'
      ? { institute_email: String(data.get('email')), password: String(data.get('password')) }
      : { name: String(data.get('name')), institute_email: String(data.get('email')), password: String(data.get('password')), role: String(data.get('role')) }
    try {
      if (mode === 'register') {
        await api<User>('/auth/register', undefined, {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        const login = await api<{ access_token: string }>('/auth/login', undefined, {
          method: 'POST',
          body: JSON.stringify({ institute_email: payload.institute_email, password: payload.password }),
        })
        onAuthenticated(login.access_token)
      } else {
        const result = await api<{ access_token: string }>('/auth/login', undefined, {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        onAuthenticated(result.access_token)
      }
      navigate('/dashboard')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to authenticate')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <p className="eyebrow">IITM BS</p>
        <h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
        <p className="auth-subtitle">{mode === 'login' ? 'Sign in to continue to mentoring.' : 'Use your institute email to join the platform.'}</p>
        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && <>
            <label>Full name<input name="name" autoComplete="name" minLength={2} required /></label>
            <label>Account role<select name="role" defaultValue="student"><option value="student">Student</option><option value="mentor">Mentor</option></select></label>
          </>}
          <label>Institute email<input name="email" type="email" autoComplete="email" required /></label>
          <label>Password<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={8} required /></label>
          {error && <p className="error-message" role="alert">{error}</p>}
          <button type="submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Register'}</button>
        </form>
        <Link to="/" className="back-link">← Back home</Link>
      </div>
    </main>
  )
}

function DashboardPage({ user, token, onLogout }: { user: User; token: string; onLogout: () => void }) {
  const [data, setData] = useState<DashboardData>({
    mentors: [], requests: [], relationships: [], questions: [], recommendations: [], notifications: [], users: [], applications: [], reports: [], analytics: {}, alerts: { stale_requests: [], inactive_relationships: [] },
  })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const notifications = await api<{ items: NotificationItem[] }>('/notifications', token)
      const common = { notifications: notifications.items }
      if (user.role === 'student') {
        const [mentors, requests, relationships, questions, recommendations] = await Promise.all([
          api<{ items: Mentor[] }>('/mentors/search?page=1&page_size=30'),
          api<{ items: MentoringRequest[] }>('/requests', token),
          api<{ items: Relationship[] }>('/relationships', token),
          api<Question[]>('/students/questions', token),
          api<{ recommendations: Recommendation[] }>('/matching/recommendations', token).catch(() => ({ recommendations: [] })),
        ])
        setData(current => ({ ...current, ...common, mentors: mentors.items, requests: requests.items, relationships: relationships.items, questions, recommendations: recommendations.recommendations }))
      } else if (user.role === 'mentor') {
        const [requests, relationships] = await Promise.all([
          api<{ items: MentoringRequest[] }>('/requests', token),
          api<{ items: Relationship[] }>('/relationships', token),
        ])
        setData(current => ({ ...current, ...common, requests: requests.items, relationships: relationships.items }))
      } else {
        const [users, applications, reports, analytics, alerts] = await Promise.all([
          api<{ items: AdminUser[] }>('/admin/users', token),
          api<Application[]>('/admin/applications', token),
          api<{ items: Report[] }>('/admin/reports', token),
          api<Record<string, number>>('/admin/analytics', token),
          api<DashboardData['alerts']>('/admin/alerts', token),
        ])
        setData(current => ({ ...current, ...common, users: users.items, applications, reports: reports.items, analytics, alerts }))
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load dashboard')
    }
  }, [token, user.role])

  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function act(path: string, body?: unknown, method = 'POST') {
    setError('')
    setNotice('')
    setBusy(true)
    try {
      await api(path, token, { method, ...(body === undefined ? {} : { body: JSON.stringify(body) }) })
      setNotice('Your changes have been saved.')
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page-shell dashboard-shell">
      <header className="topbar">
        <div><p className="eyebrow">{user.role} workspace</p><h1>Hello, {user.name}</h1><p className="auth-subtitle">{user.institute_email}</p></div>
        <nav className="nav-actions"><button className="secondary-btn" onClick={() => void load()} disabled={busy}>Refresh</button><button className="secondary-btn" onClick={onLogout}>Sign out</button></nav>
      </header>
      {error && <p className="error-message" role="alert">{error}</p>}
      {notice && <p className="success-message" role="status">{notice}</p>}
      {user.role === 'student' && <StudentWorkspace user={user} data={data} token={token} busy={busy} act={act} refreshMentors={mentors => setData(current => ({ ...current, mentors }))} />}
      {user.role === 'mentor' && <MentorWorkspace data={data} token={token} busy={busy} act={act} />}
      {user.role === 'admin' && <AdminWorkspace data={data} busy={busy} act={act} />}
      <section className="panel"><div className="section-heading"><h2>Notifications</h2><p>Updates for your account and mentoring activity.</p></div>
        {data.notifications.length === 0 ? <p className="empty-state">No notifications yet.</p> : data.notifications.map(item => (
          <div className="list-row" key={item.id}><span>{item.message}</span><span className="status-badge">{item.is_read ? 'Read' : 'New'}</span>{!item.is_read && <button className="text-button" onClick={() => void act(`/notifications/${item.id}/read`)}>Mark read</button>}</div>
        ))}
      </section>
    </main>
  )
}

function StudentWorkspace({ user, data, token, busy, act, refreshMentors }: { user: User; data: DashboardData; token: string; busy: boolean; act: (path: string, body?: unknown, method?: string) => Promise<void>; refreshMentors: (mentors: Mentor[]) => void }) {
  const [selectedMentor, setSelectedMentor] = useState<number | null>(null)
  const [profile, setProfile] = useState({ career_goal: '', current_situation: '', preferred_language: '', weekly_availability: '', career_aspirations: '' })
  const [question, setQuestion] = useState('')
  const [requestMessage, setRequestMessage] = useState('')
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [filters, setFilters] = useState({ query: '', domain: '', guidance_type: '', industry: '', graduation_year: '', language: '', experience_level: '' })
  const [searchError, setSearchError] = useState('')
  useEffect(() => {
    void api<typeof profile>('/students/me/profile', token).then(value => setProfile(current => ({ ...current, ...value }))).catch(() => undefined)
  }, [token])

  return <>
    <section className="panel">
      <div className="section-heading"><h2>Your career profile</h2><p>Keep this up to date so mentors can understand your goals.</p></div>
      <form className="form-grid" onSubmit={event => { event.preventDefault(); void act('/students/me/profile', { ...profile, interest_area_ids: [] }, 'PUT') }}>
        <label>Career goal<input value={profile.career_goal} onChange={event => setProfile({ ...profile, career_goal: event.target.value })} maxLength={1000} /></label>
        <label>Current situation<input value={profile.current_situation} onChange={event => setProfile({ ...profile, current_situation: event.target.value })} maxLength={1000} /></label>
        <label>Preferred language<input value={profile.preferred_language} onChange={event => setProfile({ ...profile, preferred_language: event.target.value })} maxLength={100} /></label>
        <label>Weekly availability<input value={profile.weekly_availability} onChange={event => setProfile({ ...profile, weekly_availability: event.target.value })} maxLength={1000} /></label>
        <label className="wide-field">Career aspirations<textarea value={profile.career_aspirations} onChange={event => setProfile({ ...profile, career_aspirations: event.target.value })} maxLength={2000} /></label>
        <button type="submit" disabled={busy}>Save profile</button>
      </form>
    </section>
    <section className="panel">
      <div className="section-heading"><h2>Career questions</h2><p>Share a specific question to include with your mentor requests.</p></div>
      <form className="inline-form" onSubmit={event => { event.preventDefault(); void act('/students/questions', { question_text: question }).then(() => setQuestion('')) }}>
        <label className="grow-field">Your question<textarea value={question} onChange={event => setQuestion(event.target.value)} minLength={50} maxLength={500} required /></label>
        <button type="submit" disabled={busy}>Add question</button>
      </form>
      {data.questions.map(item => <p className="list-row" key={item.id}>{item.question_text}</p>)}
    </section>
    <section className="panel">
      <div className="section-heading"><h2>Discover mentors</h2><p>Approved mentors accepting new requests.</p></div>
      <form className="form-grid filter-grid" onSubmit={event => {
        event.preventDefault()
        const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value.trim()).map(([key, value]) => [key, value]))
        void api<{ items: Mentor[] }>(`/mentors/search?${params.toString()}`).then(result => { refreshMentors(result.items); setSearchError('') }).catch(reason => setSearchError(reason instanceof Error ? reason.message : 'Mentor search failed'))
      }}>
        <label>Keywords<input value={filters.query} onChange={event => setFilters({ ...filters, query: event.target.value })} /></label>
        <label>Domain<input value={filters.domain} onChange={event => setFilters({ ...filters, domain: event.target.value })} /></label>
        <label>Guidance type<input value={filters.guidance_type} onChange={event => setFilters({ ...filters, guidance_type: event.target.value })} /></label>
        <label>Industry<input value={filters.industry} onChange={event => setFilters({ ...filters, industry: event.target.value })} /></label>
        <label>Graduation year<input type="number" value={filters.graduation_year} onChange={event => setFilters({ ...filters, graduation_year: event.target.value })} /></label>
        <label>Language<input value={filters.language} onChange={event => setFilters({ ...filters, language: event.target.value })} /></label>
        <label>Experience level<select value={filters.experience_level} onChange={event => setFilters({ ...filters, experience_level: event.target.value })}><option value="">Any experience</option><option>Recent Graduate</option><option>Experienced</option><option>Senior</option></select></label>
        <button type="submit">Search mentors</button>
      </form>
      {searchError && <p className="error-message" role="alert">{searchError}</p>}
      {data.recommendations.length > 0 && <div className="recommendation-list"><h3>Recommended for you</h3>{data.recommendations.map(item => <p key={item.mentor_id}><strong>{item.mentor_name}</strong> · {item.match_score}% match · {item.match_explanation.join(', ')}</p>)}</div>}
      {data.mentors.length === 0 ? <p className="empty-state">No mentors are available right now.</p> : <div className="card-grid">{data.mentors.map(mentor => <article className="feature-card" key={mentor.id}>
        <h3>{mentor.name}</h3><p>{mentor.experience_level} · {mentor.roles || 'Career guidance'}</p><p>{mentor.guidance_types || mentor.organisations || 'Profile details coming soon'}</p>
        <button type="button" className="primary-btn" onClick={() => setSelectedMentor(mentor.user_id)}>Request mentoring</button>
      </article>)}</div>}
      {selectedMentor !== null && <form className="inline-form request-form" onSubmit={event => {
        event.preventDefault()
        void act('/requests', { mentor_id: selectedMentor, personal_message: requestMessage, career_question_id: selectedQuestion ? Number(selectedQuestion) : null }).then(() => { setSelectedMentor(null); setRequestMessage(''); setSelectedQuestion('') })
      }}>
        <label className="grow-field">Personal message (100–1,000 characters)
          <textarea value={requestMessage} onChange={event => setRequestMessage(event.target.value)} minLength={100} maxLength={1000} required />
        </label>
        {data.questions.length > 0 && <label>Career question<select value={selectedQuestion} onChange={event => setSelectedQuestion(event.target.value)}><option value="">No question attached</option>{data.questions.map(item => <option value={item.id} key={item.id}>{item.question_text}</option>)}</select></label>}
        <button type="submit" disabled={busy}>Send request</button><button className="secondary-btn" type="button" onClick={() => setSelectedMentor(null)}>Cancel</button>
      </form>}
    </section>
    <section className="panel"><div className="section-heading"><h2>Your requests</h2></div>
      {data.requests.length === 0 ? <p className="empty-state">You have not sent a mentoring request yet.</p> : data.requests.map(item => <div className="list-row" key={item.id}>
        <span>{data.mentors.find(mentor => mentor.user_id === item.mentor_id)?.name || `Mentor #${item.mentor_id}`}</span><span className="status-badge">{item.status}</span>{item.status === 'pending' && <button className="text-button" onClick={() => void act(`/requests/${item.id}/withdraw`)}>Withdraw</button>}
      </div>)}
    </section>
    <RelationshipPanels data={data} token={token} user={user} act={act} busy={busy} />
  </>
}

function RelationshipPanels({ data, token, user, act, busy }: { data: DashboardData; token: string; user: User; act: (path: string, body?: unknown, method?: string) => Promise<void>; busy: boolean }) {
  const [selected, setSelected] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [sessionTime, setSessionTime] = useState('')
  const [noteText, setNoteText] = useState('')
  const [reportText, setReportText] = useState('')
  const [history, setHistory] = useState<{
    messages: { id: number; sender_id: number; content: string }[]
    sessions: { id: number; status: string; scheduled_for: string | null; proposer_id: number }[]
    notes: Record<number, { id: number; notes: string; submitted_late: boolean }[]>
  }>({ messages: [], sessions: [], notes: {} })
  useEffect(() => {
    if (selected === null) return
    void Promise.all([
      api<{ items: { id: number; sender_id: number; content: string }[] }>(`/relationships/${selected}/messages`, token),
      api<{ items: { id: number; status: string; scheduled_for: string | null; proposer_id: number }[] }>(`/relationships/${selected}/sessions`, token),
    ]).then(async ([messages, sessions]) => {
      const notes = await Promise.all(sessions.items.map(async session => {
        const response = await api<{ items: { id: number; notes: string; submitted_late: boolean }[] }>(`/sessions/${session.id}/notes`, token)
        return [session.id, response.items] as const
      }))
      setHistory({ messages: messages.items, sessions: sessions.items, notes: Object.fromEntries(notes) })
    }).catch(() => setHistory({ messages: [], sessions: [], notes: {} }))
  }, [selected, token, data.relationships])

  return <section className="panel"><div className="section-heading"><h2>{user.role === 'student' ? 'Your mentors' : 'Assigned mentees'}</h2><p>Session scheduling and conversation history for your relationships.</p></div>
    {data.relationships.length === 0 ? <p className="empty-state">No mentoring relationships yet.</p> : data.relationships.map(item => {
      const other = user.role === 'student' ? item.mentor_name : item.student_name
      const otherUserId = user.role === 'student' ? item.mentor_id : item.student_id
      return <article className="relationship-card" key={item.id}>
        <div className="list-row"><strong>{other}</strong><span className="status-badge">{item.status}</span><button className="text-button" onClick={() => setSelected(item.id)}>Open relationship</button></div>
        <p>{user.role === 'student'
          ? [item.mentor_career_history, item.mentor_expertise?.length ? `Expertise: ${item.mentor_expertise.join(', ')}` : null].filter(Boolean).join(' · ')
          : [item.student_career_goal, item.student_interests?.length ? `Interests: ${item.student_interests.join(', ')}` : null, item.current_question ? `Question: ${item.current_question}` : null].filter(Boolean).join(' · ')}</p>
        {selected === item.id && <>
          <div className="conversation">
            {history.messages.length === 0 ? <p className="empty-state">No messages yet.</p> : history.messages.map(row => <p className="message-bubble" key={row.id}><strong>{row.sender_id === user.id ? 'You' : other}</strong>: {row.content}</p>)}
          </div>
          {item.status === 'active' && <form className="inline-form" onSubmit={event => { event.preventDefault(); void act(`/relationships/${item.id}/messages`, { content: message }).then(() => setMessage('')) }}>
            <label className="grow-field">Message<textarea value={message} onChange={event => setMessage(event.target.value)} maxLength={2000} required /></label><button disabled={busy}>Send</button>
          </form>}
          {item.status === 'active' && <form className="inline-form" onSubmit={event => {
            event.preventDefault()
            void act(`/relationships/${item.id}/sessions`, { scheduled_for: new Date(sessionTime).toISOString(), timezone: Intl.DateTimeFormat().resolvedOptions().timeZone }).then(() => setSessionTime(''))
          }}>
            <label>Propose a session<input type="datetime-local" value={sessionTime} onChange={event => setSessionTime(event.target.value)} required /></label><button disabled={busy}>Propose session</button>
          </form>}
          {history.sessions.map(session => <div className="session-card" key={session.id}>
            <div className="list-row"><span>{session.scheduled_for ? new Date(session.scheduled_for).toLocaleString() : 'Unscheduled'}</span><span className="status-badge">{session.status}</span>
              {session.status === 'proposed' && session.proposer_id !== user.id && <button className="text-button" onClick={() => void act(`/sessions/${session.id}/decision`, { action: 'confirm' })}>Confirm</button>}
              {session.status === 'proposed' && session.proposer_id === user.id && <span className="muted-copy">Waiting for the other participant</span>}
              {session.status === 'confirmed' && session.scheduled_for && new Date(session.scheduled_for) < new Date() && <button className="text-button" onClick={() => void act(`/sessions/${session.id}/decision`, { action: 'complete' })}>Mark complete</button>}
            </div>
            {(history.notes[session.id] || []).map(note => <p className="message-bubble" key={note.id}>{note.notes}{note.submitted_late ? ' · Submitted late' : ''}</p>)}
            <form className="inline-form" onSubmit={event => { event.preventDefault(); void act(`/sessions/${session.id}/notes`, { notes: noteText }).then(() => setNoteText('')) }}>
              <label className="grow-field">Session notes<textarea value={noteText} onChange={event => setNoteText(event.target.value)} maxLength={10000} required /></label><button disabled={busy}>Add note</button>
            </form>
          </div>)}
          {user.role !== 'admin' && <form className="inline-form" onSubmit={event => {
            event.preventDefault()
            void act('/reports', { target_user_id: otherUserId, category: 'OTHER', description: reportText }).then(() => setReportText(''))
          }}>
            <label className="grow-field">Report {other}<textarea value={reportText} onChange={event => setReportText(event.target.value)} minLength={20} maxLength={4000} required /></label><button className="secondary-btn" disabled={busy}>Submit report</button>
          </form>}
          {item.status === 'active' && <button className="text-button danger-text" onClick={() => void act(`/relationships/${item.id}/close`, { reason: 'NO_LONGER_NEEDED' })}>Close relationship</button>}
        </>}
      </article>
    })}
  </section>
}

function MentorWorkspace({ data, token, busy, act }: { data: DashboardData; token: string; busy: boolean; act: (path: string, body?: unknown, method?: string) => Promise<void> }) {
  const [declineReason, setDeclineReason] = useState('')
  const [applicationState, setApplicationState] = useState('')
  const [profile, setProfile] = useState({ career_history: '', organisations: '', roles: '', years_of_experience: 0, experience_level: 'Recent Graduate', guidance_types: '', preferred_languages: '', max_mentee_capacity: 1, pause_status: 'active' })
  useEffect(() => { void api<typeof profile & { status: string }>('/mentors/me/profile', token).then(value => setProfile(current => ({ ...current, ...value }))).catch(() => undefined) }, [token])
  return <>
    <section className="panel"><div className="section-heading"><h2>Mentor application</h2><p>Submit your details for administrator review.</p></div>
      <form className="form-grid" onSubmit={event => {
        event.preventDefault()
        const formData = new FormData(event.currentTarget)
        const body = { roll_number: String(formData.get('roll')), graduation_year: Number(formData.get('graduation')) || null, additional_verification_info: String(formData.get('verification')) }
        void act('/mentors/apply', body).then(() => setApplicationState('Application submitted'))
      }}>
        <label>Roll number<input name="roll" maxLength={50} /></label><label>Graduation year<input name="graduation" type="number" min={1950} max={2100} /></label>
        <label className="wide-field">Verification information<textarea name="verification" maxLength={4000} /></label><button type="submit" disabled={busy}>Submit application</button>
      </form>{applicationState && <p role="status">{applicationState}</p>}
    </section>
    <section className="panel"><div className="section-heading"><h2>Mentor profile and availability</h2></div>
      <form className="form-grid" onSubmit={event => { event.preventDefault(); void act('/mentors/me/profile', { ...profile, expertise_area_ids: [] }, 'PUT') }}>
        <label>Career history<textarea value={profile.career_history} onChange={event => setProfile({ ...profile, career_history: event.target.value })} maxLength={4000} /></label>
        <label>Organisations<input value={profile.organisations} onChange={event => setProfile({ ...profile, organisations: event.target.value })} maxLength={2000} /></label>
        <label>Roles<input value={profile.roles} onChange={event => setProfile({ ...profile, roles: event.target.value })} maxLength={2000} /></label>
        <label>Guidance offered<input value={profile.guidance_types} onChange={event => setProfile({ ...profile, guidance_types: event.target.value })} maxLength={2000} /></label>
        <label>Maximum mentees<input type="number" min={1} max={5} value={profile.max_mentee_capacity} onChange={event => setProfile({ ...profile, max_mentee_capacity: Number(event.target.value) })} /></label>
        <label>Availability<select value={profile.pause_status} onChange={event => setProfile({ ...profile, pause_status: event.target.value })}><option value="active">Available</option><option value="paused">Paused</option></select></label>
        <button type="submit" disabled={busy}>Save mentor profile</button>
      </form>
    </section>
    <section className="panel"><div className="section-heading"><h2>Incoming requests</h2></div>
      {data.requests.filter(item => item.status === 'pending').length === 0 ? <p className="empty-state">No pending requests.</p> : data.requests.filter(item => item.status === 'pending').map(item => <article className="relationship-card" key={item.id}>
        <h3>{item.student?.name || `Student #${item.student_id}`}</h3><p>{item.student?.career_goal || item.student?.current_situation || 'No profile details shared yet.'}</p><p>{item.student?.career_question || 'No career question attached.'}</p><p>{item.personal_message}</p>
        <div className="inline-form"><label className="grow-field">Optional decline reason<textarea value={declineReason} onChange={event => setDeclineReason(event.target.value)} maxLength={1000} /></label>
          <button disabled={busy} onClick={() => void act(`/requests/${item.id}/decision`, { action: 'accept' })}>Accept</button>
          <button className="secondary-btn" disabled={busy} onClick={() => void act(`/requests/${item.id}/decision`, { action: 'decline', decline_reason: declineReason }).then(() => setDeclineReason(''))}>Decline</button>
        </div>
      </article>)}
    </section>
    <RelationshipPanels data={data} token={token} user={{ id: 0, name: '', institute_email: '', role: 'mentor', account_status: '' }} act={act} busy={busy} />
  </>
}

function AdminWorkspace({ data, busy, act }: { data: DashboardData; busy: boolean; act: (path: string, body?: unknown, method?: string) => Promise<void> }) {
  return <>
    <section className="panel"><div className="section-heading"><h2>Program overview</h2><p>Aggregated activity; private conversations and notes are not shown.</p></div>
      <div className="stats-grid">{[['Active mentors', data.analytics.active_mentors], ['Active mentees', data.analytics.active_mentees], ['Relationships', data.analytics.active_relationships], ['Sessions', data.analytics.sessions], ['Request acceptance', `${Math.round((data.analytics.acceptance_rate || 0) * 100)}%`]].map(([label, value]) => <div className="stat-tile" key={String(label)}><strong>{value}</strong><span>{label}</span></div>)}</div>
      <p className="muted-copy">{data.alerts.stale_requests.length} requests pending over five days · {data.alerts.inactive_relationships.length} inactive relationships</p>
    </section>
    <section className="panel"><div className="section-heading"><h2>Mentor applications</h2></div>
      {data.applications.filter(application => application.status === 'pending').length === 0 ? <p className="empty-state">No applications awaiting review.</p> : data.applications.filter(application => application.status === 'pending').map(application => <div className="list-row" key={application.id}><span>Application #{application.id} · User #{application.user_id}</span>
        <button disabled={busy} onClick={() => void act(`/admin/applications/${application.id}/review`, { action: 'approve' })}>Approve</button>
        <button className="secondary-btn" disabled={busy} onClick={() => void act(`/admin/applications/${application.id}/review`, { action: 'reject', rejection_reason: 'Application did not meet verification requirements.' })}>Reject</button>
      </div>)}
    </section>
    <section className="panel"><div className="section-heading"><h2>Reports</h2></div>
      {data.reports.length === 0 ? <p className="empty-state">No reports submitted.</p> : data.reports.map(report => <article className="relationship-card" key={report.id}><p>Report #{report.id} · {report.category} · User #{report.target_user_id} · {report.status}</p><p>{report.description}</p>
        {report.status !== 'resolved' && report.status !== 'dismissed' && <div className="inline-form"><button disabled={busy} onClick={() => void act(`/admin/reports/${report.id}/review`, { status: 'resolved', admin_review_notes: 'Reviewed by administrator.' })}>Resolve</button><button className="secondary-btn" disabled={busy} onClick={() => void act(`/admin/reports/${report.id}/review`, { status: 'dismissed', admin_review_notes: 'Reviewed; no policy violation was identified.' })}>Dismiss</button></div>}
      </article>)}
    </section>
    <section className="panel"><div className="section-heading"><h2>User management</h2><p>Suspending an account pauses active relationships; reactivation resumes them only if the other participant is active.</p></div>
      {data.users.map(item => <div className="list-row" key={item.id}><span>{item.name} · {item.role} · {item.account_status}</span>
        {item.account_status === 'suspended'
          ? <button disabled={busy} onClick={() => void act(`/admin/users/${item.id}/reactivate`, { reason: 'Administrator reviewed the account and approved reactivation.' })}>Reactivate</button>
          : item.role !== 'admin' && <button className="secondary-btn" disabled={busy} onClick={() => void act(`/admin/users/${item.id}/suspend`, { reason: 'Administrator review requires a temporary suspension.' })}>Suspend</button>}
      </div>)}
    </section>
  </>
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('mentoring_token') || '')
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token))
  const navigate = useNavigate()

  useEffect(() => {
    if (!token) return
    void api<User>('/auth/me', token).then(setUser).catch(() => {
      localStorage.removeItem('mentoring_token')
      setToken('')
      setUser(null)
    }).finally(() => setLoading(false))
  }, [token])

  function authenticated(value: string) {
    localStorage.setItem('mentoring_token', value)
    setLoading(true)
    setToken(value)
  }

  function logout() {
    localStorage.removeItem('mentoring_token')
    setToken('')
    setUser(null)
    navigate('/')
  }

  if (loading) return <main className="auth-shell"><p role="status">Loading your workspace…</p></main>
  return <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/login" element={<AuthPage mode="login" onAuthenticated={authenticated} />} />
    <Route path="/register" element={<AuthPage mode="register" onAuthenticated={authenticated} />} />
    <Route path="/dashboard" element={user && token ? <DashboardPage user={user} token={token} onLogout={logout} /> : <AuthPage mode="login" onAuthenticated={authenticated} />} />
    <Route path="*" element={<HomePage />} />
  </Routes>
}

export default App
