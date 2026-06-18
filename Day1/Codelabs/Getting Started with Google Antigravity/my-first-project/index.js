#!/usr/bin/env node

import Parser from 'rss-parser';
import chalk from 'chalk';
import { program } from 'commander';

// Initialize the RSS Parser
const parser = new Parser();

// Configure CLI Options
program
  .name('google-news')
  .description('A CLI tool to fetch the latest news from Google News')
  .version('1.0.0')
  .option('-s, --search <query>', 'Search query for Google News')
  .option('-l, --limit <number>', 'Number of news items to show', parseInt, 10)
  .parse(process.argv);

const options = program.opts();

// Construct the correct feed URL
let feedUrl = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en';
if (options.search) {
  const query = encodeURIComponent(options.search);
  feedUrl = `https://news.google.com/rss/search?q=${query}&hl=en-US&gl=US&ceid=US:en`;
}

async function fetchNews() {
  console.log(chalk.blue.bold('\n🔄 Fetching latest news from Google News...'));
  
  try {
    const feed = await parser.parseURL(feedUrl);
    
    console.log(chalk.green.bold('✔ Successfully loaded feed!\n'));
    
    const titleText = options.search 
      ? `Search results for: "${options.search}"` 
      : 'Top Stories';
    
    console.log(chalk.bgBlue.white.bold(` ${titleText.toUpperCase()} `));
    console.log(chalk.gray('━'.repeat(60)));

    const items = feed.items.slice(0, options.limit);
    
    if (items.length === 0) {
      console.log(chalk.yellow('No news items found. Try a different search term.'));
      return;
    }

    items.forEach((item, index) => {
      // Google News titles are usually formatted as "Title text - Source Name"
      // Let's try to extract the source cleanly
      let title = item.title || 'No Title';
      let source = 'Google News';
      
      const sourceMatch = title.match(/(.*) - ([^-]+)$/);
      if (sourceMatch) {
        title = sourceMatch[1].trim();
        source = sourceMatch[2].trim();
      }

      // Format publication date
      const pubDate = item.pubDate ? new Date(item.pubDate).toLocaleString() : 'Unknown date';

      console.log(`${chalk.cyan.bold(index + 1 + '.')} ${chalk.white.bold(title)}`);
      console.log(`   ${chalk.yellow('Source:')} ${chalk.green(source)}   ${chalk.yellow('Published:')} ${chalk.gray(pubDate)}`);
      console.log(`   ${chalk.blue.underline(item.link)}\n`);
    });

    console.log(chalk.gray('━'.repeat(60)));
    console.log(chalk.dim(`Showing ${items.length} of ${feed.items.length} items.`));
    console.log();
  } catch (error) {
    console.error(chalk.red.bold('\n❌ Error fetching news feed:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

fetchNews();
