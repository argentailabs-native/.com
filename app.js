const groups = [
  { id: 1, name: "Bio Study Collective", course: "BIO 201", members: 4, times: ["Tue afternoon", "Wed evening"], style: "Active discussion", format: "In-person", place: "Science Library", color: "peach", initials: "BC" },
  { id: 2, name: "Cell Squad", course: "BIO 201", members: 3, times: ["Wed evening", "Thu afternoon"], style: "Active discussion", format: "In-person", place: "Student Center", color: "teal", initials: "CS" },
  { id: 3, name: "Bio Focus Room", course: "BIO 201", members: 5, times: ["Tue afternoon", "Fri morning"], style: "Quiet review", format: "Virtual", place: "Google Meet", color: "yellow", initials: "BF" },
  { id: 4, name: "Molecule Makers", course: "CHEM 101", members: 4, times: ["Mon morning", "Wed evening"], style: "Active discussion", format: "In-person", place: "Chemistry Hall", color: "teal", initials: "MM" },
  { id: 5, name: "Chem Cram", course: "CHEM 101", members: 6, times: ["Tue afternoon", "Thu afternoon"], style: "Quiet review", format: "Virtual", place: "Zoom", color: "peach", initials: "CC" },
  { id: 6, name: "Code & Coffee", course: "CS 150", members: 3, times: ["Mon morning", "Fri morning"], style: "Active discussion", format: "In-person", place: "Engineering Lab", color: "yellow", initials: "C&" },
  { id: 7, name: "Debug Buddies", course: "CS 150", members: 5, times: ["Wed evening", "Thu afternoon"], style: "Active discussion", format: "Virtual", place: "Discord", color: "teal", initials: "DB" },
  { id: 8, name: "Silent Syntax", course: "CS 150", members: 2, times: ["Tue afternoon", "Wed evening"], style: "Quiet review", format: "In-person", place: "Main Library", color: "peach", initials: "SS" }
];

function findMatches(preferences) {
  return groups.filter(group => group.course === preferences.course).map(group => {
    const overlap = group.times.filter(time => preferences.times.includes(time));
    const score = Math.min(99, 55 + overlap.length * 16 + (group.style === preferences.style ? 12 : 0) + (group.format === preferences.format ? 10 : 0));
    return { ...group, overlap, score };
  }).filter(group => group.overlap.length > 0).sort((a, b) => b.score - a.score);
}

function currentPreferences() {
  return {
    course: document.querySelector("#course").value,
    times: [...document.querySelectorAll('#times input:checked')].map(input => input.value),
    style: document.querySelector('input[name="style"]:checked').value,
    format: document.querySelector('input[name="format"]:checked').value
  };
}

function renderMatches() {
  const matches = findMatches(currentPreferences());
  const results = document.querySelector("#results");
  const empty = document.querySelector("#empty-state");
  document.querySelector("#result-count").textContent = `${matches.length} match${matches.length === 1 ? "" : "es"} found`;
  empty.hidden = matches.length !== 0;
  results.innerHTML = matches.map((group, index) => `
    <article class="result-card ${index === 0 ? "best" : ""}">
      ${index === 0 ? '<span class="best-label">BEST MATCH</span>' : ""}
      <div class="result-head"><span class="group-avatar ${group.color}">${group.initials}</span><div><h3>${group.name}</h3><p>${group.course} · ${group.members} members</p></div><strong>${group.score}%<small>match</small></strong></div>
      <div class="tags"><span>◷ ${group.overlap.join(" + ")}</span><span>${group.style === "Active discussion" ? "☁" : "☕"} ${group.style}</span><span>${group.format === "In-person" ? "⌖" : "▣"} ${group.format}</span></div>
      <div class="card-bottom"><span>${group.place}</span><button type="button" data-group="${group.name}">Request to join <span>→</span></button></div>
    </article>`).join("");

  results.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
    button.innerHTML = "Request sent <span>✓</span>";
    button.classList.add("sent");
    button.disabled = true;
  }));
}

if (typeof document !== "undefined") {
  document.querySelector("#match-form").addEventListener("change", renderMatches);
  document.querySelector("#match-form").addEventListener("submit", event => { event.preventDefault(); renderMatches(); document.querySelector(".results-panel").scrollIntoView({ behavior: "smooth", block: "center" }); });
  renderMatches();
}

if (typeof module !== "undefined") module.exports = { findMatches, groups };
