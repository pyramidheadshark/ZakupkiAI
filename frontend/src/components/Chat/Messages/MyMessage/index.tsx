import { useEffect, useState } from 'react'
import './style.scss'

interface Props{
  children: JSX.Element|JSX.Element[]|string
}
console.log(window.innerWidth)
function MyMessage({children}: Props) {
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
        <span>
          {children}
        </span>
      </>
      :
      <>
        <span>
          {children}
        </span>
        <img src="../../../../../public/ic_person1.png" alt="" />
      </>
      }
    </div>
  )
}

export default MyMessage
