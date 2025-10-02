import React from "react";

interface ButtonProps
  extends React.DetailedHTMLProps<
    React.HTMLAttributes<HTMLDivElement>,
    HTMLDivElement
  > {
  children: React.ReactNode;
  className?: string;
}

export const Button = (props: ButtonProps) => {
  const { children, className, ...divProps } = props;
  return (
    <div
      className={
        "w-max h-8 flex items-center gap-2 px-2 py-1 bg-sky-900 rounded font-bold text-white text-[14px] shadow-lg hover:bg-sky-700 cursor-pointer " +
        className
      }
      {...divProps}
    >
      {children}
    </div>
  );
};
