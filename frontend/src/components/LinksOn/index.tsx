import './style.scss'
import Link from './Link'
import More from './More'

function LinksOn() {
  const links = [
    {
      name: "Как работает КТРУ"
    },
    {
      name: "Как чат-бот связан с закупками",
    },
    {
      name: "Что такое федеральные закупки"
    },
    {
      name: "Как чат-бот связан с закупками"
    }
  ]
  return (
    <div id="LinksOn">
        <div className='exo2 FAQ'>Часто задаваемые вопросы</div>
        <div className="Links exo">
            <div>
              <div>44-ФЗ</div>
              <div>223-ФЗ</div>
            </div>
            {links.map((link, i) => 
                <Link key={i}>{link.name}</Link>)
            }     
        </div>
        <More />
    </div>
  )
}

export default LinksOn