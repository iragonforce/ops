(() => {
  'use strict';
  const labels = {local: 'Local network', tailscale: 'Tailscale', external: 'External'};
  const storageKey = 'homelab-link-mode';
  let inventory = null;
  let override = localStorage.getItem(storageKey) || 'auto';
  let active = null;
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  const guessed = () => location.hostname.endsWith('.ts.net') ? 'tailscale'
    : /^(192\.168\.|127\.)/.test(location.hostname) || location.hostname.endsWith('.homelab.lan') ? 'local' : 'external';
  function positionNetworkBar(bar) {
    const nav = document.querySelector(
      '.header .desktop-navigation'
    );
    const main = document.querySelector('.body-content')
      || document.body;

    // Keep the original content placement on smaller screens.
    const wide = window.matchMedia(
      '(min-width: 1280px)'
    ).matches;

    if (wide && nav) {
      if (bar.previousElementSibling !== nav) {
        nav.after(bar);
      }
    } else if (main.firstElementChild !== bar) {
      main.prepend(bar);
    }
  }

  function banner() {
    let bar = document.getElementById('homelab-network-bar');
    if (bar) {
      positionNetworkBar(bar);
      return bar;
    }
    bar = node('aside', undefined, 'homelab-network-bar');
    bar.id = 'homelab-network-bar';
    bar.append(node('strong', 'Service links'));
    const label = node('span'); label.id = 'homelab-network-label'; bar.append(label);
    const select = node('select'); select.setAttribute('aria-label', 'Choose service network');
    for (const value of ['auto', 'local', 'tailscale', 'external']) {
      const option = node('option', value === 'auto' ? 'Automatic' : labels[value]);
      option.value = value; select.append(option);
    }
    select.value = override;
    select.addEventListener('change', () => {override = select.value; localStorage.setItem(storageKey, override); refresh();});
    bar.append(select);
    positionNetworkBar(bar);
    return bar;
  }
  const serviceIconById = Object.freeze({
  "nexus-cockpit": "cockpit",
  "tensor-cockpit": "cockpit",
  "nexus-sync": "syncthing",
  "tensor-syncthing": "syncthing",
  "iot": "home-assistant",
  "nexus-jellyfin": "jellyfin",
  "nexus-grafana": "grafana",
  "nexus-checkmk": "checkmk",
  "nexus-dashboard": "glance"
});

  function card(service, status, mode) {
    const result = node('article', undefined, 'homelab-service');
    const preferred = service.urls[mode];
    const usable = preferred && status?.state !== 'unpublished';

    const title = node(
      usable ? 'a' : 'span',
      service.name,
      'homelab-service-name'
    );

    if (usable) {
      title.href = preferred;
      title.target = '_blank';
      title.rel = 'noopener noreferrer';
    }
    const identity = node(
      'div', undefined, 'homelab-service-identity'
    );

    const initials = service.name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map(part => part.charAt(0))
      .join('')
      .toUpperCase();

    const mark = node(
      'span', initials || 'S', 'homelab-service-mark'
    );
    mark.setAttribute('aria-hidden', 'true');

    const iconSlug = serviceIconById[service.id];

    if (iconSlug) {
      const img = node(
        'img', undefined, 'homelab-service-icon'
      );

      img.src = '/assets/icons/' + iconSlug + '.png?v=phase4';
      img.alt = '';
      img.decoding = 'async';

      img.addEventListener('error', () => {
        mark.replaceChildren(
          document.createTextNode(initials || 'S')
        );
        mark.classList.remove('has-icon');
      }, {once: true});

      mark.replaceChildren(img);
      mark.classList.add('has-icon');
    }

    identity.append(mark, title);
    result.append(identity);

    const current = !preferred
      ? {state: 'private', label: 'No URL for selected network'}
      : status || {state: 'unknown', label: 'Checking'};

    result.append(node(
      'span',
      labels[mode] + ': ' + current.label,
      'homelab-status status-' + current.state
    ));

    const links = node('div', undefined, 'homelab-service-links');

    for (const key of ['local', 'tailscale', 'external']) {
      const url = service.urls[key];
      const blocked = key === mode &&
        status?.state === 'unpublished';
      const enabled = Boolean(url) && !blocked;

      const names = {
        local: 'Local',
        tailscale: 'Tailscale',
        external: 'External'
      };

      const link = node(
        enabled ? 'a' : 'span',
        names[key],
        'homelab-service-link' +
          (key === mode ? ' is-preferred' : '') +
          (!enabled ? ' is-missing' : '')
      );

      if (enabled) {
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.title = url;
      } else {
        link.title = blocked
          ? 'No public DNS confirmed'
          : 'No configured URL';
      }

      links.append(link);
    }

    result.append(links);

    if (service.note) {
      result.append(node(
        'small',
        service.note,
        'homelab-service-note'
      ));
    }

    return result;
  }

  function render(data) {
    inventory = data;
    active = override === 'auto' ? data.detected : override;
    banner();
    document.getElementById('homelab-network-label').textContent = labels[active]
      + (override === 'auto' ? ' · detected connection' : ' · manual selection');
    for (const root of document.querySelectorAll('[data-homelab-services]')) {
      const scope = root.dataset.homelabServices;
      root.replaceChildren();

      if (root.dataset.featured && scope === 'all') {
        const overview = node(
          'div', undefined, 'homelab-overview'
        );

        for (const host of ['nexus', 'tensor']) {
          const entries = data.services.filter(
            service => service.host === host
          );

          const configured = entries.filter(
            service => Boolean(service.urls[active])
          );

          // Endpoint reachability, not host/container health.
          const counts = {
            up: 0, protected: 0, down: 0, other: 0
          };

          for (const service of configured) {
            const state = data.status?.[service.id]?.state;

            if (state === 'up' ||
                state === 'protected' ||
                state === 'down') {
              counts[state]++;
            } else {
              counts.other++;
            }
          }

          const tile = node(
            'div', undefined, 'homelab-overview-tile'
          );

          tile.append(node(
            'span',
            host === 'nexus' ? 'NEXUS' : 'TENSOR',
            'homelab-overview-label'
          ));

          tile.append(node(
            'strong',
            configured.length + ' / ' +
              entries.length + ' URLs',
            'homelab-overview-value'
          ));

          tile.append(node(
            'small',
            data.checked_at
              ? [
                  counts.up + ' reachable',
                  counts.protected + ' auth',
                  counts.down + ' down',
                  ...(counts.other
                    ? [counts.other + ' other']
                    : [])
                ].join(' · ')
              : 'Endpoint status unavailable',
            'homelab-overview-detail'
          ));

          // Blinkwired Phase 5: Git and infrastructure.
          // Endpoint reachability, not host health.
          if (data.checked_at && configured.length > 0) {
            const meter = node(
              'div', undefined, 'homelab-endpoint-meter'
            );

            const summary = [
              counts.up + ' reachable',
              counts.protected + ' authentication-protected',
              counts.down + ' down',
              counts.other + ' other'
            ].join(', ');

            meter.setAttribute('role', 'img');
            meter.setAttribute(
              'aria-label',
              'Endpoint checks: ' + summary
            );

            for (const [state, count] of [
              ['up', counts.up],
              ['protected', counts.protected],
              ['down', counts.down],
              ['other', counts.other]
            ]) {
              if (count <= 0) continue;

              const segment = node(
                'span',
                undefined,
                'homelab-meter-segment meter-' + state
              );

              segment.style.flexGrow = String(count);
              segment.title = state + ': ' + count;

              meter.append(segment);
            }

            tile.append(meter);
          }

          overview.append(tile);
        }

        const total = node(
          'div', undefined, 'homelab-overview-tile'
        );

        total.append(node(
          'span', 'CATALOG', 'homelab-overview-label'
        ));

        total.append(node(
          'strong',
          data.services.length + ' entries',
          'homelab-overview-value'
        ));

        total.append(node(
          'small',
          data.services.filter(s => s.featured).length +
            ' featured · ' +
            data.services.filter(
              s => Boolean(s.urls[active])
            ).length + ' configured URLs',
          'homelab-overview-detail'
        ));

        overview.append(total);

        const gitTile = node(
          'div',
          undefined,
          'homelab-overview-tile homelab-git-tile'
        );

        gitTile.append(node(
          'span',
          'SOURCE CONTROL',
          'homelab-overview-label'
        ));

        gitTile.append(node(
          'strong',
          'Git / ops',
          'homelab-overview-value'
        ));

        gitTile.append(node(
          'small',
          'Infrastructure source of truth',
          'homelab-overview-detail'
        ));

        const gitLink = node(
          'a',
          'Open iragonforce/ops',
          'homelab-git-link'
        );

        gitLink.href =
          'https://github.com/iragonforce/ops';

        gitLink.target = '_blank';
        gitLink.rel = 'noopener noreferrer';

        gitTile.append(gitLink);
        overview.append(gitTile);

        root.append(overview);
      }

      if (data.checked_at) root.append(node('p', 'Endpoint checks: ' + new Date(data.checked_at * 1000).toLocaleTimeString()
        + '. “Protected” means authentication is required; it does not confirm the application behind it.', 'homelab-check-note'));
      for (const host of ['nexus', 'tensor']) {
        if (scope !== 'all' && scope !== host) continue;
        const section = node('section'); section.append(node('h2', host === 'nexus' ? 'Nexus' : 'Tensor'));
        const grid = node('div', undefined, 'homelab-services-grid');
        const services = data.services.filter(s => s.host === host && (!root.dataset.featured || s.featured));
        const linked = services.filter(s =>
          Object.values(s.urls).some(Boolean));
        const internal = services.filter(s =>
          !Object.values(s.urls).some(Boolean));

        for (const service of linked) {
          grid.append(card(service, data.status?.[service.id], active));
        }

        section.append(grid);

        if (internal.length) {
          const details = node('details', undefined, 'homelab-internal');
          details.append(node(
            'summary',
            'Internal containers / no web URL (' + internal.length + ')'
          ));

          const internalGrid = node(
            'div', undefined, 'homelab-services-grid'
          );

          for (const service of internal) {
            internalGrid.append(card(
              service, data.status?.[service.id], active
            ));
          }

          details.append(internalGrid);
          section.append(details);
        }

        root.append(section);
      }
    }
    rewriteLinks();
  }
  function rewriteLinks() {
    if (!inventory) return;
    const matches = new Map();
    for (const service of inventory.services) for (const alias of service.aliases || []) matches.set(alias, service);
    for (const anchor of document.querySelectorAll('a[href],a[data-homelab-original]')) {
      if (anchor.closest('[data-homelab-services]') || anchor.closest('.homelab-network-bar')) continue;
      const original = anchor.dataset.homelabOriginal || anchor.getAttribute('href');
      let hostname;
      try {hostname = new URL(original, location.href).hostname;} catch {continue;}
      const service = matches.get(hostname);
      if (service) {
        anchor.dataset.homelabOriginal = original;
        const url = service.urls[active];
        if (url) {if (anchor.getAttribute('href') !== url) anchor.setAttribute('href', url); anchor.removeAttribute('aria-disabled');}
        else {anchor.removeAttribute('href'); anchor.setAttribute('aria-disabled', 'true'); anchor.title = 'Unavailable on selected network';}
      } else if (hostname.endsWith('.homelab.io') && !anchor.dataset.homelabOriginal) {
        anchor.dataset.homelabOriginal = original;
        anchor.removeAttribute('href'); anchor.setAttribute('aria-disabled', 'true'); anchor.title = 'Retired service address';
      }
    }
  }
  async function refresh() {
    try {
      let response = await fetch('/__homelab/context', {cache: 'no-store'});
      if (!response.ok) throw new Error('Context unavailable');
      let data = await response.json();
      const mode = override === 'auto' ? data.detected : override;
      if (data.mode !== mode) {
        response = await fetch('/__homelab/context?mode=' + encodeURIComponent(mode), {cache: 'no-store'});
        if (!response.ok) throw new Error('Status unavailable');
        data = await response.json();
      }
      render(data);
    } catch {
      if (!inventory) {
        try {
          const response = await fetch('/assets/homelab-services.json', {cache: 'no-store'});
          const data = await response.json();
          render({...data, detected: guessed(), mode: guessed(), status: {}});
          document.getElementById('homelab-network-label').textContent += ' · status unavailable';
        } catch {banner(); document.getElementById('homelab-network-label').textContent = 'Dashboard connection unavailable';}
      }
    }
  }
  function start() {
    banner(); refresh();
    new MutationObserver(() => rewriteLinks()).observe(document.body, {childList: true, subtree: true});
    setInterval(() => {if (!document.hidden) refresh();}, 30000);
    window.matchMedia('(min-width: 1280px)')
      .addEventListener('change', () => {
        const bar = document.getElementById(
          'homelab-network-bar'
        );
        if (bar) positionNetworkBar(bar);
      });
    window.addEventListener('online', refresh);
    document.addEventListener('visibilitychange', () => {if (!document.hidden) refresh();});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
