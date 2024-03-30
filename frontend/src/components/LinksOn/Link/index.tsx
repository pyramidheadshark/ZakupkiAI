import { useState } from 'react'
import './style.scss'

interface Props {
  href: string
  children: string
}

function Link({href, children}: Props) {


  return (
    <a href={href} className="Link">
        {children}
    </a>
  )
}

export default Link