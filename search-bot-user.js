const { searchFiles } = require('./gdrive-lib.js');

async function main() {
  console.log("Searching for 'bot_user' or 'Bot_user' in Google Drive...");
  
  // Search for anything with name containing bot_user or Bot_user
  const results1 = await searchFiles("name contains 'bot_user' and trashed = false");
  const results2 = await searchFiles("name contains 'Bot_user' and trashed = false");
  const results3 = await searchFiles("name contains 'botuser' and trashed = false");

  // Merge results and de-duplicate by ID
  const map = new Map();
  [...results1.files, ...results2.files, ...results3.files].forEach(f => {
    map.set(f.id, f);
  });

  console.log("SEARCH RESULTS:");
  console.log(JSON.stringify(Array.from(map.values()), null, 2));
}

main().catch(console.error);
