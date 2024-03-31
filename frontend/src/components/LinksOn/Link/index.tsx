import { useDispatch } from 'react-redux'
import './style.scss'
import { setMsgs } from '../../../store/redusers/chatSlice'
import { textPush } from '../../../http/API'

interface Props {
  href: string
  children: string
}

function Link({href, children}: Props) {

  const dispatch = useDispatch()
  
  async function sendMessage() {
    const date = new Date(Date.now())
    const time = date.getHours() + ":" + date.getMinutes()
    dispatch(setMsgs({who: "me", msg: children, time}))
    dispatch(setMsgs({who: "bot", msg: "...", time}))

    const federalLaw = "44-ФЗ"

    textPush(children, federalLaw).then((response) => {
      const date = new Date(Date.now())
      const time = date.getHours() + ":" + date.getMinutes()
      dispatch(setMsgs({who: "bot", msg: response.msg as string, time}))
    })

  }

  return (
    <button className="Link" onClick={sendMessage}>
        {children}
    </button>
  )
}

export default Link