import { NavLink } from 'react-router-dom';
import { useAuth } from '../state/auth';

const links = [
    { to: "/", label: "Shop", end: true },
        { to: '/cart', label: 'Cart', protected: true },
        { to: '/orders', label: 'Orders', protected: true },
        { to: '/login', label: 'Login', guestOnly: true },
        { to: '/register', label: 'Register', guestOnly: true },
];

export default function Header() {
    const { isAuthenticated, logout } = useAuth();
    const visibleLinks = links.filter((link) => (
        (!link.protected || isAuthenticated) && (!link.guestOnly || !isAuthenticated)
    ));

    return <header className="site-header">
        <div className="brand">Sneaker Shop</div>
    <nav>
                <ul className="nav-list">
                        {visibleLinks.map((link) => (
                <li key={link.to}>
                    <NavLink to={link.to} end={link.end} className={({ isActive }) => isActive ? 'active' : undefined}>
                        {link.label}
                    </NavLink>
                </li>
            ))}
        </ul>
    </nav>
    {isAuthenticated && <button onClick={logout}>Log out</button>}
  </header>;
}
