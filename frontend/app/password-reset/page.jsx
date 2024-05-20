"use client";
import LandingLayout from "@/layouts/LandingLayout";
import Link from "next/link";
import { useEffect, useState } from "react";


const breaks = Array(10).fill(0).map((_, i) => <br key={i} />); // borrar cuando se haga el login


const page = () => {
  useEffect(() => {
    document.querySelector("body").classList.add("home-three");
  }, []);
  const [active, setActive] = useState("collapse1");
  return (
    <LandingLayout header footer bodyClass={"home-three"} onePage>
      {/* Signup area start */}
      <section
        className="hero-area-three bgs-cover bgc-lighter pt-210 rpt-150 pb-100"
      >
        <div className="container">
          <div className="d-flex justify-content-center">
            <h3>Password Reset</h3>
            {breaks} {/*borrar cuando se haga el login*/}      

          </div>
        </div>
      </section>
      {/* Signup area End */}
    </LandingLayout>
  );
};
export default page;