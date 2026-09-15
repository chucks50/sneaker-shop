import {NavLink} from "react-router-dom";

const links = [
    { to: "/", label: "Shop", end: true },
    { to: "/cart", label: "Cart" },
    {to: '/orders', label: 'Orders'},
    { to: "/login", label: "Login" },
];


export default function Header() {
  return <header ClassName="site-header">
    <div className="Brand">sneaker shop</div>
    <nav>
        <ul classname="nav-lists">
            {links.map((link) => (
                <li key={link.to}>
                    <NavLink to={link.to} end={link.end} className={({ isActive }) => isActive ? 'active' : undefined}>
                        {link.label}
                    </NavLink>
                </li>
            ))}
        </ul>
    </nav>
  </header>;
}
