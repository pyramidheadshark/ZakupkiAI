import './style.scss'
import logo from "../../../../../public/icon_rua.svg"
interface Props{
  children: JSX.Element|JSX.Element[]|string
}

function BotMessage({children}: Props) {
  return (
    <div className="BotMessage exo">
        <img src={logo} alt="" />
        <span>
          {children}
        </span>
    </div>
  )
}

export default BotMessage
