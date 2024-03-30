import './style.scss'
import Link from './Link'
import More from './More'

function LinksOn() {
  const links = [
    {
      name: "Как работает КТРУ",
      href: "https://fz.ru/"
    },
    {
      name: "Как чат-бот  связан с закупками",
      href: "https://fz.ru/"
    },
    {
      name: "Как работает КТРУ",
      href: "https://fz.ru/"
    },
    {
      name: "Что такое федеральные закупки",
      href: "https://fz.ru/"
    },
    {
      name: "Как чат-бот связан с закупками",
      href: "https://fz.ru/"
    }
  ]
  return (
    <div id="LinksOn">
        <div className='exo2 FAQ'>Часто задаваемые вопросы</div>
        <div className="Links">
            <div>
              <div>44-ФЗ</div>
              <div>223-ФЗ</div>
            </div>
            {links.map((link, i) => <Link key={i} href={link.href}>{link.name}</Link>)}     
        </div>
        <More />
    </div>
  )
}

export default LinksOn