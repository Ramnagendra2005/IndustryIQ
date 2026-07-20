import React from "react";

/**
 * IndustryIQ icon set — hand-drawn 24px stroke icons, 1.5px stroke,
 * rounded caps. Consistent visual language across the whole app.
 * Usage: <IconGraph className="w-4 h-4" />  (color via currentColor)
 */

function I({ children, className = "w-4 h-4", ...rest }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  );
}

export const IconGraph = (p) => (
  <I {...p}>
    <circle cx="6" cy="6" r="2.4" />
    <circle cx="18" cy="8" r="2.4" />
    <circle cx="12" cy="18" r="2.4" />
    <path d="M8.2 6.8l7.4 0.8M7 8.2l4 7.6M16.8 10l-3.6 6" />
  </I>
);

export const IconDocs = (p) => (
  <I {...p}>
    <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9.5A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z" />
    <path d="M14 3.5V8h4.5M8.5 12h7M8.5 15.5h7" />
  </I>
);

export const IconShield = (p) => (
  <I {...p}>
    <path d="M12 3l7 3v5.5c0 4.5-3 7.7-7 9.5-4-1.8-7-5-7-9.5V6l7-3Z" />
    <path d="M9 12l2.2 2.2L15.5 9.8" />
  </I>
);

export const IconUpload = (p) => (
  <I {...p}>
    <path d="M12 15V4.5M8 8l4-3.5L16 8" />
    <path d="M4.5 15.5V18a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-2.5" />
  </I>
);

export const IconChat = (p) => (
  <I {...p}>
    <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v7a2.5 2.5 0 0 1-2.5 2.5H12l-4.5 4v-4h-1A2.5 2.5 0 0 1 4 13.5v-7Z" />
    <path d="M8 9h8M8 12h5" />
  </I>
);

export const IconBolt = (p) => (
  <I {...p}>
    <path d="M13 2.5L5 13.5h5.5L11 21.5l8-11h-5.5L13 2.5Z" />
  </I>
);

export const IconPump = (p) => (
  <I {...p}>
    <circle cx="10" cy="13" r="5.5" />
    <circle cx="10" cy="13" r="1.6" />
    <path d="M10 7.5V4.5M7 4.5h6M15.5 13h5M18 10.5l2.5 2.5L18 15.5" />
  </I>
);

export const IconWrench = (p) => (
  <I {...p}>
    <path d="M14.5 6.5a4 4 0 0 1 5-3.9l-2.8 2.8 2 2 2.8-2.8a4 4 0 0 1-5.4 4.6L8 17.3A2.1 2.1 0 1 1 5 14.3l7.3-8.1a4 4 0 0 1 2.2-1.7" />
  </I>
);

export const IconSearch = (p) => (
  <I {...p}>
    <circle cx="10.5" cy="10.5" r="6" />
    <path d="M15 15l5.5 5.5" />
  </I>
);

export const IconAlert = (p) => (
  <I {...p}>
    <path d="M12 3.5l9 16h-18l9-16Z" />
    <path d="M12 10v4M12 17.2v.3" />
  </I>
);

export const IconManual = (p) => (
  <I {...p}>
    <path d="M4.5 5A1.5 1.5 0 0 1 6 3.5h5v17H6A1.5 1.5 0 0 1 4.5 19V5Z" />
    <path d="M19.5 5A1.5 1.5 0 0 0 18 3.5h-5v17h5a1.5 1.5 0 0 0 1.5-1.5V5Z" />
    <path d="M7 8h1.5M15.5 8H17M7 11h1.5M15.5 11H17" />
  </I>
);

export const IconIncident = (p) => (
  <I {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5v5M12 15.8v.3" />
  </I>
);

export const IconSOP = (p) => (
  <I {...p}>
    <rect x="5" y="3.5" width="14" height="17" rx="1.5" />
    <path d="M9 8h6M9 11.5h6M9 15h3.5" />
    <path d="M9 3.5v-1M15 3.5v-1" />
  </I>
);

export const IconRegulation = (p) => (
  <I {...p}>
    <path d="M12 4v16M12 4l-6.5 2M12 4l6.5 2" />
    <path d="M3.5 11.5L5.5 6l2 5.5a3 3 0 0 1-4 0ZM16.5 11.5L18.5 6l2 5.5a3 3 0 0 1-4 0Z" />
    <path d="M8.5 20h7" />
  </I>
);

export const IconSheet = (p) => (
  <I {...p}>
    <rect x="4" y="4.5" width="16" height="15" rx="1.5" />
    <path d="M4 9.5h16M9.5 9.5v10M4 14.5h16" />
  </I>
);

export const IconMail = (p) => (
  <I {...p}>
    <rect x="3.5" y="5.5" width="17" height="13" rx="1.8" />
    <path d="M4.5 7l7.5 6 7.5-6" />
  </I>
);

export const IconMap = (p) => (
  <I {...p}>
    <path d="M9 4.5L4 6.5v13l5-2 6 2 5-2v-13l-5 2-6-2Z" />
    <path d="M9 4.5v13M15 6.5v13" />
  </I>
);

export const IconSend = (p) => (
  <I {...p}>
    <path d="M4 12l16-7.5L15 20l-3-6.5L4 12Z" />
    <path d="M12 13.5l8-9" />
  </I>
);

export const IconBrain = (p) => (
  <I {...p}>
    <circle cx="12" cy="12" r="2" />
    <circle cx="5.5" cy="8" r="1.8" />
    <circle cx="18.5" cy="7" r="1.8" />
    <circle cx="6.5" cy="17" r="1.8" />
    <circle cx="17.5" cy="17.5" r="1.8" />
    <path d="M7.2 8.8l3.2 2.1M16.9 8.2l-3.1 2.3M7.9 16l2.6-2.5M16.2 16.4l-2.7-2.7" />
  </I>
);

export const IconField = (p) => (
  <I {...p}>
    <rect x="7.5" y="3" width="9" height="18" rx="2" />
    <path d="M10.5 18.5h3" />
  </I>
);

export const IconDesktop = (p) => (
  <I {...p}>
    <rect x="3.5" y="4.5" width="17" height="12" rx="1.5" />
    <path d="M9 20h6M12 16.5V20" />
  </I>
);

export const IconClock = (p) => (
  <I {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3 2" />
  </I>
);

export const IconCheck = (p) => (
  <I {...p}>
    <path d="M4.5 12.5l5 5 10-11" />
  </I>
);

export const IconArrowLeft = (p) => (
  <I {...p}>
    <path d="M19 12H5M10.5 6.5L5 12l5.5 5.5" />
  </I>
);

export const IconMicroscope = (p) => (
  <I {...p}>
    <path d="M6.5 20.5h11M9 17.5h6" />
    <path d="M10 13.5l-2-2 6.5-6.5 2 2L10 13.5Z" />
    <path d="M13 14.5a5 5 0 0 0 3.5-8.4" />
    <path d="M9.5 3.5l2 2" />
  </I>
);

export const IconCalendar = (p) => (
  <I {...p}>
    <rect x="4" y="5" width="16" height="15.5" rx="1.5" />
    <path d="M4 9.5h16M8.5 3v3.5M15.5 3v3.5" />
  </I>
);

export const IconFactory = (p) => (
  <I {...p}>
    <path d="M3.5 20.5V10l5.5 3.5V10l5.5 3.5V6.5h5v14h-16Z" />
    <path d="M17 10.5v.3M17 14v.3M7 17h.3M11 17h.3" />
  </I>
);

export const IconImage = (p) => (
  <I {...p}>
    <rect x="3.5" y="4.5" width="17" height="15" rx="1.8" />
    <circle cx="9" cy="10" r="1.6" />
    <path d="M4.5 17.5l4.5-4 3 2.7 4-4 3.5 3.3" />
  </I>
);

export const IconScale = (p) => (
  <I {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 6.5v6l3.5 3.5" />
    <path d="M12 3.5v-1M20.5 12h1M12 20.5v1M3.5 12h-1" />
  </I>
);

export const IconConflict = (p) => (
  <I {...p}>
    <path d="M8 4.5h8M8 4.5L5 12l3 7.5M16 4.5l3 7.5-3 7.5M8 19.5h8" />
    <path d="M12 8.5v4M12 15.3v.3" />
  </I>
);

export const IconDoc = (p) => (
  <I {...p}>
    <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9.5A1.5 1.5 0 0 1 5.5 19V5A1.5 1.5 0 0 1 7 3.5Z" />
    <path d="M14 3.5V8h4.5" />
  </I>
);

/** doc_type → icon component (replaces the old emoji map) */
export const DOCTYPE_ICONS = {
  "P&ID": IconMap,
  WorkOrder: IconWrench,
  InspectionReport: IconSearch,
  OEMManual: IconManual,
  IncidentReport: IconIncident,
  SOP: IconSOP,
  RegulatoryDocument: IconRegulation,
  Spreadsheet: IconSheet,
  Email: IconMail,
  Other: IconDoc,
};

/** Convenience renderer: <DocTypeIcon type="WorkOrder" className="w-4 h-4" /> */
export function DocTypeIcon({ type, className = "w-4 h-4", ...rest }) {
  const C = DOCTYPE_ICONS[type] || IconDoc;
  return <C className={className} {...rest} />;
}

/** doc_type → tint color for icon plates */
export const DOCTYPE_TINT = {
  "P&ID": "#38bdf8",
  WorkOrder: "#f5a623",
  InspectionReport: "#60a5fa",
  OEMManual: "#c084fc",
  IncidentReport: "#f87171",
  SOP: "#34d399",
  RegulatoryDocument: "#2dd4bf",
  Spreadsheet: "#fbbf24",
  Email: "#94a3b8",
  Other: "#94a3b8",
};
