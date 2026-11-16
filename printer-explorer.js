(() => {
  const parts = [
    ['Repaired · July 6', 'Replacing the extruder', 'A broken bearing in the filament-loading assembly stopped the first setup attempt. After ordering a compatible replacement, I installed the new extruder and got filament feeding again.', 'IMG_7420.jpeg', 'Installed replacement extruder assembly'],
    ['Repaired · July 6', 'The gear mismatch', 'My stepper had a press-fit gear, rather than the removable screw-mounted variant. The first replacement kit did not match. I reordered the kit and used adhesive foam under the gear to help the gears mesh.', 'IMG_7434.jpeg', 'Stepper motor with the press-fit gear'],
    ['Printing · July 6', 'From failed prints to Benchy', 'With the extruder working, I spent the evening tuning print settings. The next day produced a calibration cube and a Benchy: the first successful test prints of the restoration.', 'IMG_7446.jpeg', 'The first Benchy test print'],
    ['Planned · Winter', 'Back on the workbench', 'A BLTouch sensor and replacement hotend are waiting for the next round of work. A Raspberry Pi print server is also planned, so files will no longer need to be loaded manually with an SD card. These upgrades are not installed yet.', null, '']
  ];
  const detail = document.querySelector('#printer-detail');
  function select(index) {
    const [status, title, copy, photo, alt] = parts[index];
    detail.replaceChildren();
    for (const [tag, text, cls] of [['p', status, 'project-kicker'], ['h3', title, ''], ['p', copy, '']]) {
      const node = document.createElement(tag); node.textContent = text; node.className = cls; detail.append(node);
    }
    if (photo) { const img = document.createElement('img'); img.src = '../imgs/' + photo; img.alt = alt; detail.append(img); }
    document.querySelectorAll('[data-part]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.part) === index)));
  }
  document.querySelectorAll('[data-part]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.part))));
  select(0);
})();
