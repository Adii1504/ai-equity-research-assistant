// profile.js — Complete Profile Management with instant UI sync & PostgreSQL persistence
window.__PROFILE_JS_ACTIVE = true;

document.addEventListener("DOMContentLoaded", async () => {
  const pageStatus = document.getElementById("pageStatus");
  const profileCard = document.getElementById("profileCard");
  const logoutBtn = document.getElementById("logoutBtn");
  const profileEmail = document.getElementById("profileEmail");
  const profileAvatar = document.getElementById("profileAvatar");
  const profileAmount = document.getElementById("profileAmount");
  const profileRegion = document.getElementById("profileRegion");
  const profileValidity = document.getElementById("profileValidity");
  const profileCreated = document.getElementById("profileCreated");

  const fundAmountInput = document.getElementById("fundAmountInput");
  const fundsForm = document.getElementById("fundsForm");
  const addFundsBtn = document.getElementById("addFundsBtn");
  const setBalanceBtn = document.getElementById("setBalanceBtn");
  const fundsStatusMsg = document.getElementById("fundsStatusMsg");
  const quickFundBtns = document.querySelectorAll(".quick-fund-btn");

  const regionForm = document.getElementById("regionForm");
  const regionSelect = document.getElementById("regionSelect");
  const customRegionInput = document.getElementById("customRegionInput");
  const regionStatusMsg = document.getElementById("regionStatusMsg");

  // Helper to format currency in Indian Rupees (₹)
  function formatRupees(amount) {
    const num = Number(amount) || 0;
    return `₹${num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  // Get current stored state
  let token = localStorage.getItem("fingo_token") || localStorage.getItem("financecla_token");
  let currentAmount = parseFloat(localStorage.getItem("financecla_user_amount") || "0") || 0;
  let currentRegion = localStorage.getItem("financecla_user_region") || "India (NSE / BSE)";
  let isAuth = false;
  let profileData = null;

  // Visual updater for Amount
  function updateAmountDisplay(newAmount) {
    const val = parseFloat(newAmount) || 0;
    currentAmount = val;
    localStorage.setItem("financecla_user_amount", String(val));

    if (profileAmount) {
      profileAmount.textContent = formatRupees(val);
      profileAmount.style.color = "#34d399";
      profileAmount.style.transition = "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)";
      profileAmount.style.transform = "scale(1.08)";
      setTimeout(() => {
        profileAmount.style.transform = "scale(1)";
      }, 250);
    }
  }

  // Visual updater for Region
  function updateRegionDisplay(newRegion) {
    if (!newRegion) return;
    currentRegion = newRegion;
    localStorage.setItem("financecla_user_region", newRegion);

    if (profileRegion) {
      profileRegion.textContent = newRegion;
      profileRegion.style.color = "#10b981";
      profileRegion.style.transition = "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)";
      profileRegion.style.transform = "scale(1.06)";
      setTimeout(() => {
        profileRegion.style.transform = "scale(1)";
      }, 250);
    }
  }

  // ── 1. Fetch Profile Data ──────────────────────────────────────
  if (token) {
    try {
      const res = await fetch("/api/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        isAuth = true;
        profileData = await res.json();
        if (profileData.amount !== undefined) currentAmount = Number(profileData.amount) || 0;
        if (profileData.region) currentRegion = profileData.region;
      }
    } catch (err) {
      console.warn("Could not reach /api/auth/me, using local profile:", err);
    }
  }

  // Fallbacks if not logged in
  const emailVal = (profileData && profileData.email) || localStorage.getItem("financecla_user_email") || "Guest Trader";
  const createdVal = (profileData && profileData.created_at) ? new Date(profileData.created_at).toLocaleDateString() : new Date().toLocaleDateString();

  if (pageStatus) pageStatus.classList.add("hidden");
  if (profileCard) profileCard.classList.remove("hidden");

  if (profileEmail) profileEmail.textContent = emailVal;
  if (profileAvatar) profileAvatar.textContent = emailVal.charAt(0).toUpperCase();
  if (profileValidity) profileValidity.textContent = isAuth ? "PAN CARD" : "Local Verified";
  if (profileCreated) profileCreated.textContent = createdVal;

  updateAmountDisplay(currentAmount);
  updateRegionDisplay(currentRegion);

  // Sync region select dropdown
  if (regionSelect) {
    for (let opt of regionSelect.options) {
      if (opt.value.toLowerCase() === currentRegion.toLowerCase() || opt.text.toLowerCase() === currentRegion.toLowerCase()) {
        regionSelect.value = opt.value;
        break;
      }
    }
  }

  // ── 2. Quick Amount Chip Handlers ──────────────────────────────
  quickFundBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      quickFundBtns.forEach(b => b.style.borderColor = "var(--border)");
      btn.style.borderColor = "var(--brand)";
      const val = btn.getAttribute("data-val");
      if (fundAmountInput && val) {
        fundAmountInput.value = val;
        fundAmountInput.focus();
      }
    });
  });

  // ── 3. Fund Processing Logic ───────────────────────────────────
  async function processFunds(isDeposit) {
    if (!fundAmountInput) return;
    let inputVal = parseFloat(fundAmountInput.value);

    if (isNaN(inputVal) || inputVal <= 0) {
      if (fundsStatusMsg) {
        fundsStatusMsg.textContent = "Please enter or pick a valid positive amount.";
        fundsStatusMsg.style.color = "#fb7185";
        fundsStatusMsg.classList.remove("hidden");
      }
      fundAmountInput.focus();
      return;
    }

    const newCalculatedAmount = isDeposit ? (currentAmount + inputVal) : inputVal;

    // Immediately update UI for instant gratification
    updateAmountDisplay(newCalculatedAmount);

    if (fundsStatusMsg) {
      const msg = isDeposit
        ? `✓ Deposited ${formatRupees(inputVal)}! New Balance: ${formatRupees(newCalculatedAmount)}`
        : `✓ Account balance set to: ${formatRupees(newCalculatedAmount)}`;
      fundsStatusMsg.textContent = msg + (isAuth ? " " : " (Saved locally)");
      fundsStatusMsg.style.color = "#34d399";
      fundsStatusMsg.classList.remove("hidden");
    }

    // Persist to PostgreSQL if authenticated
    if (token) {
      const endpoint = isDeposit ? "/api/auth/add-funds" : "/api/auth/amount";
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({ amount: inputVal })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.amount !== undefined) {
            updateAmountDisplay(data.amount);
          }
        }
      } catch (err) {
        console.warn("Backend funds sync warning:", err);
      }
    }

    fundAmountInput.value = "";
    quickFundBtns.forEach(b => b.style.borderColor = "var(--border)");
  }

  // Handle "+ Add ₹ Funds" form submission
  if (fundsForm) {
    fundsForm.addEventListener("submit", (e) => {
      e.preventDefault();
      processFunds(true);
    });
  }

  // Handle "Set Balance" button click
  if (setBalanceBtn) {
    setBalanceBtn.addEventListener("click", (e) => {
      e.preventDefault();
      processFunds(false);
    });
  }

  // ── 4. Region Management Logic ─────────────────────────────────
  if (regionSelect) {
    regionSelect.addEventListener("change", () => {
      if (customRegionInput) customRegionInput.value = "";
      updateRegionDisplay(regionSelect.value);
    });
  }

  if (customRegionInput) {
    customRegionInput.addEventListener("input", () => {
      const val = customRegionInput.value.trim();
      updateRegionDisplay(val || (regionSelect ? regionSelect.value : "India (NSE / BSE)"));
    });
  }

  if (regionForm) {
    regionForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const chosen = (customRegionInput && customRegionInput.value.trim())
        ? customRegionInput.value.trim()
        : (regionSelect ? regionSelect.value : "India (NSE / BSE)");

      updateRegionDisplay(chosen);

      if (regionStatusMsg) {
        regionStatusMsg.textContent = `✓ Region saved as '${chosen}'` + (isAuth ? " " : " in profile!");
        regionStatusMsg.style.color = "#34d399";
        regionStatusMsg.classList.remove("hidden");
      }

      if (token) {
        try {
          await fetch("/api/auth/region", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ region: chosen })
          });
        } catch (err) {
          console.warn("Backend region sync warning:", err);
        }
      }
    });
  }

  // ── 5. Schemes Timeline Fetcher ────────────────────────────────
  const schemesTimeline = document.getElementById("schemesTimeline");
  if (schemesTimeline) {
    try {
      const schemeRes = await fetch("/find-schemes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: { amount: currentAmount, region: currentRegion } })
      });
      if (schemeRes.ok) {
        const schemesData = await schemeRes.json();
        const schemes = schemesData.schemes || [];
        if (schemes.length > 0) {
          schemesTimeline.innerHTML = schemes.map(s => `
            <div class="history-item" style="padding: 1rem; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; margin-bottom: 0.75rem; background: var(--surface-subtle);">
              <h4 style="margin: 0 0 0.4rem 0; color: #34d399;">${s.name}</h4>
              <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: var(--text-secondary);">${s.explanation}</p>
            </div>
          `).join("");
        } else {
          schemesTimeline.innerHTML = `<p class="history-empty">No eligible schemes found for your profile.</p>`;
        }
      }
    } catch (e) { }
  }

  // ── 6. Logout ──────────────────────────────────────────────────
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("fingo_token");
      localStorage.removeItem("fingo_user");
      localStorage.removeItem("fingo_profile");
      localStorage.removeItem("financecla_token");
      localStorage.removeItem("financecla_user_email");
      localStorage.removeItem("financecla_user_region");
      localStorage.removeItem("financecla_user_amount");
      window.location.href = "/";
    });
  }
});
