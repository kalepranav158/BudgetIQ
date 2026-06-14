import { NavLink, useLocation } from "react-router-dom";

const primaryLinks = [
  { to: "/upload", label: "Upload" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/transactions", label: "Transactions" },
  { to: "/mappings", label: "Mappings" },
  { to: "/health", label: "Health" }
];

const utilityLinks = [
  { to: "/summaries/daily", label: "Daily Summary" },
  { to: "/summaries/monthly", label: "Monthly Summary" }
];

function Sidebar() {
  const location = useLocation();
  const activeItem = [...primaryLinks, ...utilityLinks].find((item) => item.to === location.pathname);

  return (
    <header className="topnav">
      <div className="topnav__bar">
        <div className="topnav__brand">
          <div className="topnav__logo">B</div>
          <div>
            <div className="topnav__title">BrainIQ</div>
            <div className="topnav__subtitle">{activeItem?.label || "Spending Intelligence"}</div>
          </div>
        </div>

        <nav className="topnav__links" aria-label="Utility navigation">
          {utilityLinks.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `topnav__link${isActive ? " topnav__link--active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <nav className="hero-tabs" aria-label="Main modules">
        {primaryLinks.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `hero-tabs__item${isActive ? " hero-tabs__item--active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

export default Sidebar;
