// helpers.js
function loadProfile() {
  // First check for securely saved profile from login/signup
  const user = localStorage.getItem('fingo_user');
  if (user) {
    try { 
      return JSON.parse(user); 
    } catch (e) {
      console.error("Error parsing fingo_user", e);
    }
  }
  
  // Fall back to guest profile
  const profile = localStorage.getItem('fingo_profile');
  if (profile) {
    try { 
      return JSON.parse(profile); 
    } catch (e) {
      console.error("Error parsing fingo_profile", e);
    }
  }
  
  return null;
}

window.loadProfile = loadProfile;
