import Parser from 'rss-parser';

const extractVersionFromId = (id) => {
  const parts = (id || '').split('/');
  return parts[parts.length - 1] || 'unknown';
};

const extractAuthor = (author) => {
  if (!author) return 'Unknown';
  if (typeof author === 'string') return author;
  return author.name || 'Unknown';
};

const cleanContent = (content) => {
  if (!content || content === 'No content.') return '';
  
  return content
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
};


export function calculateVersionCode(versionString) {
  if (!versionString || typeof versionString !== 'string') {
    return 0;
  }
  
  const parts = versionString.split('.');
  
  const major = parseInt(parts[0] || 0) || 0;
  const minor = parseInt(parts[1] || 0) || 0;
  const patch = parseInt(parts[2] || 0) || 0;
  
  if (major === 0) {
    return parseFloat(`${minor}.${patch}`);
  } else {
    const combined = (major * 10) + minor;
    return parseFloat(`${combined}.${patch}`);
  }
}

export async function parseGitHubAtom(xmlContent) {
  try {
    const parser = new Parser();
    const feed = await parser.parseString(xmlContent);
    
    const releases = (feed.items || []).map(item => ({
      version: item.title.match(/\d+\.\d+\.\d+/)[0] || extractVersionFromId(item.id),
      versionCode: calculateVersionCode(item.title.match(/\d+\.\d+\.\d+/)[0] || extractVersionFromId(item.id)),
      title: item.title || '',
      link: item.link || '',
      date: item.pubDate || '',
      author: extractAuthor(item.author),
      content: cleanContent(item.content),
      isPrerelease: item.title.includes('Pre-release') || false
    }));
    
    releases.sort((a, b) => new Date(b.versionCode) - new Date(a.versionCode));
    
    return {
      repo: {
        title: feed.title,
        link: feed.link,
        updated: feed.updated
      },
      releases
    };
  } catch (error) {
    console.error('Parse error:', error);
    throw error;
  }
};