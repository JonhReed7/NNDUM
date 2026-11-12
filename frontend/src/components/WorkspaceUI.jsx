import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { artwork, figmaAsset } from '../assets/figma.js';

export function DesignIcon({ name, className = '' }) {
  return (
    <img className={`design-icon ${className}`} src={figmaAsset(name)} alt="" aria-hidden="true" />
  );
}

export function Surface({ as: Tag = 'section', art, className = '', children, ...props }) {
  return (
    <Tag
      className={`surface ${art ? 'has-artwork' : ''} ${className}`}
      style={artwork(art)}
      {...props}
    >
      {children}
    </Tag>
  );
}

export function WorkspaceButton({
  href,
  art,
  secondary = false,
  className = '',
  children,
  ...props
}) {
  const Tag = href ? 'a' : 'button';
  return (
    <Tag
      href={href}
      className={`workspace-button ${secondary ? 'workspace-button--secondary' : ''} ${art ? 'has-artwork' : ''} ${className}`}
      style={artwork(art)}
      {...(!href && { type: 'button' })}
      {...props}
    >
      {children}
    </Tag>
  );
}

export function PageHeading({
  title,
  description,
  projectName = 'Marketplace Web',
  action,
  children,
  headingId = 'page-title',
}) {
  return (
    <header className="workspace-heading">
      <p className="breadcrumbs">
        <a href="#/home?section=projects">Проекты</a>
        <span aria-hidden="true"> › </span>
        {projectName}
      </p>
      <div className="workspace-title-row">
        <div>
          <h1 id={headingId}>{title}</h1>
          <p className="workspace-description">{description}</p>
        </div>
        {action}
      </div>
      {children}
    </header>
  );
}

export function Modal({ title, onClose, children }) {
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    element.showModal();
    return () => element.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="workspace-dialog"
      aria-labelledby="dialog-title"
      onCancel={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="dialog-heading">
        <h2 id="dialog-title">{title}</h2>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Закрыть">
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
