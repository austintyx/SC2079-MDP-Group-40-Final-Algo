import React, { useEffect, useState } from "react";
import { Button } from "../../common";
import { HiOutlineStatusOnline, HiOutlineStatusOffline } from "react-icons/hi";
import toast from "react-hot-toast";
import useFetch from "../../../hooks/useFetch";

export const ServerStatus = () => {
  const [isServerOnline, setIsServerOnline] = useState(false);
  const fetch = useFetch();

  const checkServerOnlineStatus = async () => {
    try {
      const isServerOnline = await fetch.get("/");

      if (isServerOnline) {
        setIsServerOnline(true);
        toast.success("Server online!");
      }
    } catch (e) {
      setIsServerOnline(false);
      toast.error("Server offline!");
    }
  };

  useEffect(() => {
    checkServerOnlineStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex items-center justify-center mt-2 mb-4">
      <Button title="Check Server Status" onClick={checkServerOnlineStatus}>
        <span>Algorithm server is </span>
        <span
          className={`${
            isServerOnline
              ? "!text-green-500 hover:!text-green-600"
              : "!text-rose-500 hover:!text-rose-600"
          }`}
        >
          {isServerOnline ? "Online" : "Offline"}
        </span>
      </Button>
    </div>
  );
};
