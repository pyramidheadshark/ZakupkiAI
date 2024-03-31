import { useEffect, useState } from 'react'
import './style.scss'
import MsgInfo from '../MsgInfo'
import { Msg } from '../../../../Interfaces/Msg'

interface Props{
  msg: Msg
}
console.log(window.innerWidth)
function MyMessage({msg}: Props) {
  const [windowWidth, setWindowWidth] = useState(window.innerWidth)

  useEffect(() => {
    function handleResize() {
      setWindowWidth(window.innerWidth)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [window.innerWidth])

  return (
    <div className="MyMessage exo">
      {windowWidth < 587
      ?
      <>
        <img src="../../../../../public/ic_person1.png" alt="" />
        <MsgInfo msg={msg} />
      </>
      :
      <>
        <MsgInfo msg={msg}/>
        <img src="../../../../../public/ic_person1.png" alt="" />
      </>
      }
    </div>
  )
}

export default MyMessage
