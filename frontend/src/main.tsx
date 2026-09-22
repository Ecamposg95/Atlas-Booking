import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './styles.css'

type Consultant = { id: string; name: string; slug: string; booking_url?: string | null }
const linkedInProfiles: Record<string, string> = {
  'roberto-rodriguez': 'https://www.linkedin.com/in/roberto-e-rodriguez/',
  'damian-medina': 'https://www.linkedin.com/in/damianmedinalion/',
}
const api = axios.create({ baseURL: '/api' })

function App() {
  const [consultants, setConsultants] = useState<Consultant[]>([])
  const [selected, setSelected] = useState<Consultant | null>(null)
  useEffect(() => { api.get<Consultant[]>('/staff').then(({ data }) => setConsultants(data)) }, [])
  const firstName = selected?.name.split(' ')[0]
  return <main>
    <nav className="nav"><a className="wordmark" href="/">ATLAS<span>·</span>BOOKING</a><span>Consultoría privada</span></nav>
    <section className="hero"><p className="kicker">ESTRATEGIA · CLARIDAD · DECISIÓN</p><h1>Una conversación<br/><em>puede cambiarlo todo.</em></h1><p className="intro">Reserva una sesión privada con un consultor senior. Un espacio para ordenar ideas, tomar perspectiva y avanzar con intención.</p><a href="#consultores" className="hero-link">Conoce a los consultores <span>↓</span></a><div className="hero-index"><span>01</span><i/><span>ATLAS / 2026</span></div></section>
    <section id="consultores" className="consultants"><div className="section-heading"><p className="kicker">ELIGE A TU CONSULTOR</p><p>Cada sesión inicia en la agenda personal de cada profesional.</p></div><div className="consultant-grid">{consultants.map((person, index) => <button className="consultant" key={person.id} onClick={() => setSelected(person)}><div className={'portrait portrait-' + index}><span>{String(index + 1).padStart(2, '0')}</span><div className="monogram">{person.name.split(' ').map(word => word[0]).join('').slice(0, 2)}</div></div><div className="consultant-copy"><span className="role">CONSULTOR SENIOR</span><h2>{person.name}</h2><span className="explore">Ver disponibilidad <b>↗</b></span></div></button>)}</div></section>
    <section className="promise"><p className="kicker">NUESTRA FORMA DE TRABAJAR</p><h2>Menos ruido.<br/>Mejores decisiones.</h2><p>Sesiones de una hora, con el tiempo y la atención que una conversación importante requiere.</p></section>
    <footer><a className="wordmark" href="/">ATLAS<span>·</span>BOOKING</a><span>© 2026 · Ciudad de México</span><span className="atlas-tech">A product by <b>ATLAS TECH</b></span></footer>
    {selected && <div className="overlay" role="dialog" aria-modal="true" onMouseDown={() => setSelected(null)}><article className="booking-modal" onMouseDown={event => event.stopPropagation()}><button className="close" aria-label="Cerrar" onClick={() => setSelected(null)}>×</button><p className="kicker">CONSULTOR SENIOR</p><h2>Agenda con<br/><em>{firstName}.</em></h2><p>Serás dirigido a su agenda segura de Google Calendar para elegir el horario que mejor te funcione.</p><a className="profile-link" href={linkedInProfiles[selected.slug]} target="_blank" rel="noreferrer">Conocer perfil profesional en LinkedIn <span>↗</span></a>{selected.booking_url ? <a className="calendar-button" href={selected.booking_url} target="_blank" rel="noreferrer">Abrir agenda de Google <span>↗</span></a> : <div className="pending"><b>Agenda en preparación</b><span>El enlace de Google Calendar estará disponible muy pronto.</span></div>}<small>Google Calendar gestiona la disponibilidad y la confirmación de tu cita.</small></article></div>}
  </main>
}
createRoot(document.getElementById('root')!).render(<App />)
