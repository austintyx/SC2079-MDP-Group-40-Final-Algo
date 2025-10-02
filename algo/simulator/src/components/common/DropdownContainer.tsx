import React, { useState } from "react";
import { FaChevronDown, FaSitemap, FaEye, FaBrain } from "react-icons/fa";

interface DropdownContainerProps {
  itemOptions: any[];
  selectedItem: any;
  setSelectedItem: any;
}

export const DropdownContainer = (props: DropdownContainerProps) => {
  const { itemOptions, selectedItem, setSelectedItem } = props;

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative flex justify-center">
      <div className="relative min-w-[210px] bg-sky-900 text-white px-2 py-1 rounded shadow-xl">
        {/* Selector */}
        <div
          className="z-0 flex items-center justify-between gap-2 cursor-pointer"
          onClick={() => setIsOpen((prev) => !prev)}
        >
          <span className="font-bold">{selectedItem}</span>
          <FaChevronDown
            className={`w-[12px] h-[12px] ${
              isOpen && "rotate-180"
            } transition-all`}
          />
        </div>

        {/* Options */}
        <div
          className={`${
            !isOpen && "invisible translate-y-1"
          } absolute z-20 top-10 left-0 flex flex-col gap-3 bg-sky-900 px-2 py-2 rounded w-full cursor-pointer transition-all`}
        >
          {itemOptions.map((currentItem) => (
            <DropdownContainerOptions
              key={currentItem}
              itemOptions={itemOptions}
              selectedItem={selectedItem}
              setSelectedItem={setSelectedItem}
              setIsOpen={setIsOpen}
              currentItem={currentItem}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

interface DropdownContainerOptionsProps extends DropdownContainerProps {
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  currentItem: any;
}

const DropdownContainerOptions = (props: DropdownContainerOptionsProps) => {
  const { itemOptions, selectedItem, setSelectedItem, setIsOpen, currentItem } =
    props;

  return (
    <div
      className={`flex items-center gap-2 hover:bg-sky-500 hover:font-bold${
        selectedItem === currentItem && "font-bold"
      }`}
      onClick={() => {
        setIsOpen(false);
        setSelectedItem(currentItem);
      }}
    >
      <span>{currentItem}</span>
    </div>
  );
};
