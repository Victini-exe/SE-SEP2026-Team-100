import { Link, Route, Routes } from 'react-router-dom'
import './App.css'

const featureCards = [
  {
    title: 'Students',
    text: 'Build your profile, ask career questions, and discover mentors who match your goals.',
  },
  {
    title: 'Mentors',
    text: 'Share guidance, manage your expertise, and help students with industry and academic support.',
  },
  {
    title: 'Admins',
    text: 'Review applications, track mentor approvals, and keep the platform healthy and fair.',
  },
]

const processSteps = [
  'Register with your IITM email address',
  'Complete your role-specific profile',
  'Match with mentors or review applications',
  'Track progress in one mentoring dashboard',
]

const HomePage = () => (
  <main className="page-shell">
    <header className="topbar">
      <div>
        <p className="eyebrow">IITM BS</p>
        <h1>Student Mentoring Platform</h1>
      </div>
      <nav className="nav-actions">
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
      </nav>
    </header>

    <section className="hero-panel">
      <div className="hero-copy">
        <span className="pill">Career support for IITM BS students</span>
        <h2>Connect students with experienced guides and trusted mentors.</h2>
        <p>
          Build a structured mentoring experience with data-backed mentor matching, profile-based recommendations,
          and clear admin review workflows.
        </p>
        <div className="cta-row">
          <Link className="primary-btn" to="/register">
            Create account
          </Link>
          <Link className="secondary-btn" to="/login">
            Sign in
          </Link>
        </div>
      </div>
      <div className="stats-card">
        <div>
          <strong>3</strong>
          <span>Role-based journeys</span>
        </div>
        <div>
          <strong>24/7</strong>
          <span>Mentor access</span>
        </div>
        <div>
          <strong>100%</strong>
          <span>Institute email validation</span>
        </div>
      </div>
    </section>

    <section className="info-grid">
      {featureCards.map(({ title, text }) => (
        <article key={title} className="feature-card">
          <h3>{title}</h3>
          <p>{text}</p>
        </article>
      ))}
    </section>

    <section className="workflow-block">
      <div className="section-heading">
        <p className="eyebrow">How it works</p>
        <h2>Simple, structured mentoring flow</h2>
      </div>
      <div className="steps-grid">
        {processSteps.map((step, index) => (
          <div key={step} className="step-item">
            <span>{String(index + 1).padStart(2, '0')}</span>
            <p>{step}</p>
          </div>
        ))}
      </div>
    </section>
  </main>
)

const AuthCard = ({ title, subtitle, variant }: { title: string; subtitle: string; variant: 'login' | 'register' }) => (
  <main className="auth-shell">
    <div className="auth-card">
      <p className="eyebrow">IITM BS</p>
      <h1>{title}</h1>
      <p className="auth-subtitle">{subtitle}</p>
      <form className="auth-form">
        {variant === 'register' && <input type="text" placeholder="Full name" />}
        <input type="email" placeholder="Institute email" />
        <input type="password" placeholder="Password" />
        <button type="button">{title}</button>
      </form>
      <Link to="/" className="back-link">← Back home</Link>
    </div>
  </main>
)

const LoginPage = () => (
  <AuthCard title="Login" subtitle="Use your institute credentials to access your mentoring dashboard." variant="login" />
)

const RegisterPage = () => (
  <AuthCard
    title="Register"
    subtitle="Create a student or mentor account using an IITM-affiliated email address."
    variant="register"
  />
)

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App
