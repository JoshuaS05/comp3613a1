document.querySelectorAll("[data-time-picker]").forEach((picker) => {
   const input = picker.querySelector("[data-time-input]");
   const analogPicker = picker.querySelector("[data-analog-picker]");
   const clockFace = picker.querySelector("[data-clock-face]");
   const timeDisplay = picker.querySelector("[data-time-display]");
   const minuteDisplay = picker.querySelector("[data-minute-display]");
   const hint = picker.querySelector("[data-time-hint]");
   const periodButtons = [...picker.querySelectorAll("[data-period]")];
   const partButtons = [...picker.querySelectorAll("[data-time-part]")];
   const minuteAdjustButtons = [...picker.querySelectorAll("[data-minute-adjust]")];
   const state = { hour: null, minute: null, period: null, activePart: "hour" };

   const existingTime = input.value.match(/^(\d{2}):(\d{2})$/);
   if (existingTime) {
      const hour24 = Number(existingTime[1]);
      state.hour = hour24 % 12 || 12;
      state.minute = Number(existingTime[2]);
      state.period = hour24 < 12 ? "AM" : "PM";
      state.activePart = "minute";
   }

   input.removeAttribute("required");
   input.setAttribute("aria-hidden", "true");
   input.tabIndex = -1;
   input.classList.add("analog-time-picker__input--enhanced");
   analogPicker.hidden = false;

   function updateValue() {
      const hourText = state.hour === null ? "--" : String(state.hour).padStart(2, "0");
      const minuteText = state.minute === null ? "--" : String(state.minute).padStart(2, "0");
      timeDisplay.textContent = `${hourText}:${minuteText}`;
      minuteDisplay.textContent = minuteText;

      if (state.hour !== null && state.minute !== null && state.period !== null) {
         const hour24 = (state.hour % 12) + (state.period === "PM" ? 12 : 0);
         input.value = `${String(hour24).padStart(2, "0")}:${minuteText}`;
         input.dispatchEvent(new Event("input", { bubbles: true }));
         input.dispatchEvent(new Event("change", { bubbles: true }));
         hint.textContent = "Use the dial or minute controls to change the selected time.";
      } else {
         input.value = "";
         hint.textContent = "Select an hour, minute, and AM/PM.";
      }

      periodButtons.forEach((button) => {
         button.setAttribute("aria-pressed", String(button.dataset.period === state.period));
      });
      partButtons.forEach((button) => {
         button.setAttribute("aria-pressed", String(button.dataset.timePart === state.activePart));
      });
      minuteAdjustButtons.forEach((button) => {
         button.disabled = state.minute === null;
      });
      renderClockFace();
   }

   function renderClockFace() {
      const isHour = state.activePart === "hour";
      const values = isHour
         ? Array.from({ length: 12 }, (_, index) => index + 1)
         : Array.from({ length: 12 }, (_, index) => index * 5);
      clockFace.setAttribute("aria-label", isHour ? "Select hour" : "Select minute");
      clockFace.replaceChildren();

      values.forEach((value, index) => {
         const button = document.createElement("button");
         const angle = ((index / 12) * 2 * Math.PI) - (Math.PI / 2);
         const radius = 41;
         const selectedValue = isHour ? state.hour : state.minute;
         const label = isHour ? String(value) : String(value).padStart(2, "0");

         button.type = "button";
         button.className = "analog-time-picker__option";
         button.textContent = label;
         button.style.left = `${50 + radius * Math.cos(angle)}%`;
         button.style.top = `${50 + radius * Math.sin(angle)}%`;
         button.setAttribute("aria-pressed", String(selectedValue === value));
         button.setAttribute("aria-label", isHour ? `${value} o'clock` : `${label} minutes`);
         button.addEventListener("click", () => {
            if (isHour) {
               state.hour = value;
               state.activePart = "minute";
            } else {
               state.minute = value;
            }
            updateValue();
         });
         clockFace.append(button);
      });
   }

   partButtons.forEach((button) => {
      button.addEventListener("click", () => {
         state.activePart = button.dataset.timePart;
         updateValue();
      });
   });

   periodButtons.forEach((button) => {
      button.addEventListener("click", () => {
         state.period = button.dataset.period;
         updateValue();
      });
   });

   minuteAdjustButtons.forEach((button) => {
      button.addEventListener("click", () => {
         if (state.minute === null) return;
         const adjustment = Number(button.dataset.minuteAdjust);
         state.minute = (state.minute + adjustment + 60) % 60;
         updateValue();
      });
   });

   picker.closest("form").addEventListener("submit", (event) => {
      if (input.value) return;
      event.preventDefault();
      hint.textContent = "Select an hour, minute, and AM/PM before saving.";
      partButtons[0].focus();
   });

   updateValue();
});
