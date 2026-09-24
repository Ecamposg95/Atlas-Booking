import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

type Consultant = { id: string; name: string; slug: string; booking_url?: string | null }
const linkedInProfiles: Record<string, string> = {
  'roberto-rodriguez': 'https://www.linkedin.com/in/roberto-e-rodriguez/',
  'damian-medina': 'https://www.linkedin.com/in/damianmedinalion/',
}
const consultants: Consultant[] = [
  { id: 'roberto-rodriguez', name: 'Roberto Rodríguez', slug: 'roberto-rodriguez' },
  { id: 'damian-medina', name: 'Damián Medina', slug: 'damian-medina' },
]
const googleSchedulingUrls: Record<string, string | undefined> = {
  'roberto-rodriguez': undefined,
  'damian-medina': undefined,
}

declare global {
  interface Window {
    calendar?: { schedulingButton: { load: (options: { url: string; color: string; label: string; target: HTMLElement }) => void } }
  }
}

function GoogleSchedulingButton({ url }: { url: string }) {
  const target = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const loadButton = () => {
      if (!target.current || !window.calendar) return
      target.current.replaceChildren()
      window.calendar.schedulingButton.load({ url, color: '#1769aa', label: 'Programar una cita', target: target.current })
    }
    if (!document.querySelector('link[data-google-scheduling]')) {
      const stylesheet = document.createElement('link')
      stylesheet.rel = 'stylesheet'; stylesheet.href = 'https://calendar.google.com/calendar/scheduling-button-script.css'; stylesheet.dataset.googleScheduling = 'true'
      document.head.appendChild(stylesheet)
    }
    const existing = document.querySelector<HTMLScriptElement>('script[data-google-scheduling]')
    if (existing) { existing.addEventListener('load', loadButton); loadButton(); return () => existing.removeEventListener('load', loadButton) }
    const script = document.createElement('script')
    script.src = 'https://calendar.google.com/calendar/scheduling-button-script.js'; script.async = true; script.dataset.googleScheduling = 'true'; script.onload = loadButton
    document.head.appendChild(script)
  }, [url])
  return <div className="google-scheduler" ref={target}><a className="calendar-button" href={url} target="_blank" rel="noreferrer">Programar una cita <span>↗</span></a></div>
}

function App() {
  const [selected, setSelected] = useState<Consultant | null>(null)
  const firstName = selected?.name.split(' ')[0]
  return <main>
    <nav className="nav"><a className="wordmark" href="/">ATLAS<span>·</span>BOOKING</a><span>Consultoría privada</span></nav>
    <section className="hero"><p className="kicker">ESTRATEGIA · CLARIDAD · DECISIÓN</p><h1>Una conversación<br/><em>puede cambiarlo todo.</em></h1><p className="intro">Reserva una sesión privada con un consultor senior. Un espacio para ordenar ideas, tomar perspectiva y avanzar con intención.</p><a href="#consultores" className="hero-link">Conoce a los consultores <span>↓</span></a><div className="hero-index"><span>01</span><i/><span>ATLAS / 2026</span></div></section>
    <section id="consultores" className="consultants"><div className="section-heading"><p className="kicker">ELIGE A TU CONSULTOR</p><p>Cada sesión inicia en la agenda personal de cada profesional.</p></div><div className="consultant-grid">{consultants.map((person, index) => <article className="consultant" key={person.id}><div className={'portrait portrait-' + index}><span>{String(index + 1).padStart(2, '0')}</span><div className="monogram">{person.name.split(' ').map(word => word[0]).join('').slice(0, 2)}</div><div className="portrait-reveal"><span className="role">CONSULTOR SENIOR</span><h2>{person.name}</h2><div className="portrait-actions"><button onClick={() => setSelected(person)}>Agendar sesión <b>↗</b></button><a href={linkedInProfiles[person.slug]} target="_blank" rel="noreferrer">Ver LinkedIn <b>↗</b></a></div></div></div><div className="consultant-copy"><span className="role">CONSULTOR SENIOR</span><h2>{person.name}</h2><button className="explore" onClick={() => setSelected(person)}>Ver disponibilidad <b>↗</b></button></div></article>)}</div></section>
    <section className="promise"><p className="kicker">NUESTRA FORMA DE TRABAJAR</p><h2>Menos ruido.<br/>Mejores decisiones.</h2><p>Sesiones de una hora, con el tiempo y la atención que una conversación importante requiere.</p></section>
    <footer><a className="wordmark" href="/">ATLAS<span>·</span>BOOKING</a><span>© 2026 · Ciudad de México</span><span className="atlas-tech">A product by <b>ATLAS TECH</b></span></footer>
    {selected && <div className="overlay" role="dialog" aria-modal="true" onMouseDown={() => setSelected(null)}><article className="booking-modal" onMouseDown={event => event.stopPropagation()}><button className="close" aria-label="Cerrar" onClick={() => setSelected(null)}>×</button><p className="kicker">CONSULTOR SENIOR</p><h2>Agenda con<br/><em>{firstName}.</em></h2><p>Elige un horario en la agenda segura de Google Calendar.</p><a className="profile-link" href={linkedInProfiles[selected.slug]} target="_blank" rel="noreferrer">Conocer perfil profesional en LinkedIn <span>↗</span></a>{googleSchedulingUrls[selected.slug] ? <GoogleSchedulingButton key={selected.slug} url={googleSchedulingUrls[selected.slug]!} /> : <div className="pending"><b>Agenda en preparación</b><span>El enlace de Google Calendar estará disponible muy pronto.</span></div>}<small>Google Calendar gestiona la disponibilidad y la confirmación de tu cita.</small></article></div>}
  </main>
}
createRoot(document.getElementById('root')!).render(<App />)
