const fs = require('fs');
const path = require('path');

// This would typically come from a config file or an API
const phoenixConfig = {
  affiliatePrograms: {
    digitalOcean: {
      referralLink: "https://m.do.co/c/phoenix-hydra-2025",
      badgeUrl: "https://do.co/referral-badge",
      altText: "Deploy Phoenix Hydra on DigitalOcean"
    },
    customGPT: {
      referralLink: "https://customgpt.ai/?ref=phoenix-hydra",
      badgeUrl: "https://customgpt.ai/affiliate-badge",
      altText: "Phoenix Hydra + CustomGPT"
    },
    cloudflare: {
        referralLink: "https://workers.cloudflare.com/deploy/phoenix-hydra",
        badgeUrl: "https://deploy.workers.cloudflare.com/button",
        altText: "Deploy to Cloudflare Workers"
    }
  }
};

function generateMarkdownBadges() {
  const { digitalOcean, customGPT, cloudflare } = phoenixConfig.affiliatePrograms;
  
  const doBadge = `[![${digitalOcean.altText}](${digitalOcean.badgeUrl})](${digitalOcean.referralLink})`;
  const gptBadge = `[![${customGPT.altText}](${customGPT.badgeUrl})](${customGPT.referralLink})`;
  const cfBadge = `[![${cloudflare.altText}](${cloudflare.badgeUrl})](${cloudflare.referralLink})`;

  return `${doBadge}\n${gptBadge}\n${cfBadge}`;
}

async function deployBadges() {
  console.log('Generating Phoenix Hydra Monetization Badges...');
  
  const markdownBadges = generateMarkdownBadges();
  
  const readmePath = path.join(__dirname, '..', 'README.md');

  try {
    let readmeContent = fs.readFileSync(readmePath, 'utf8');
    
    // A placeholder to replace in the README.md
    const placeholder = '<!-- एफिलिएट-बैज-यहां -->'; 
    
    if (readmeContent.includes(placeholder)) {
      readmeContent = readmeContent.replace(placeholder, markdownBadges);
      fs.writeFileSync(readmePath, readmeContent, 'utf8');
      console.log('Successfully inserted badges into README.md.');
    } else {
      console.log('Placeholder not found in README.md. Appending badges to the end.');
      fs.appendFileSync(readmePath, `\n\n## Our Partners\n\n${markdownBadges}`);
    }

  } catch (error) {
    console.error('Error updating README.md:', error.message);
    console.log('Generated badges:\n', markdownBadges);
  }

  console.log('\nPhoenix Hydra Monetization Badges Deployed');
  console.log('Target Revenue 2025: €400k+');
}

deployBadges();
