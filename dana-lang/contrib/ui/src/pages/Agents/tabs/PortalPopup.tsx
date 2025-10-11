import React from 'react';
import { createPortal } from 'react-dom';

const PortalPopup: React.FC<{ children: React.ReactNode; style: React.CSSProperties }> = ({
  children,
  style,
}) => {
  return createPortal(<div style={style}>{children}</div>, document.body);
};

export default PortalPopup;
