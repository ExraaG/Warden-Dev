import React from 'react';

export interface CheckboxProps {
  id?: string;
  name?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: React.ReactNode;
  description?: React.ReactNode;
  disabled?: boolean;
  className?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  id,
  name,
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  const toggle = () => {
    if (!disabled) {
      onChange(!checked);
    }
  };

  return (
    <div
      id={id}
      role="checkbox"
      aria-checked={checked}
      tabIndex={disabled ? -1 : 0}
      onClick={toggle}
      onKeyDown={(e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          toggle();
        }
      }}
      className={`inline-flex items-start gap-2.5 cursor-pointer select-none group focus:outline-none ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${className}`}
    >
      <div
        className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 mt-0.5 transition-colors duration-150 ${
          checked
            ? 'bg-[var(--color-accent)] border-[var(--color-accent)] text-[#0d0e11]'
            : 'border-[var(--color-border)] bg-[var(--bg-main)] group-hover:border-[var(--color-accent)]/60'
        }`}
      >
        {checked && (
          <svg className="w-3 h-3 stroke-[3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>

      {(label || description) && (
        <div className="flex flex-col">
          {label && (
            <span className="text-xs font-semibold text-slate-200 group-hover:text-slate-100 transition-colors">
              {label}
            </span>
          )}
          {description && (
            <span className="text-[11px] text-slate-400 font-mono leading-tight mt-0.5">
              {description}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
