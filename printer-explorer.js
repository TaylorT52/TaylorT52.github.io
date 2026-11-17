(() => {
  const parts = [
    ['Repaired · July 6', 'Replacing the extruder', 'A broken bearing in the filament-loading assembly stopped the first setup attempt. After ordering a compatible replacement, I installed the new extruder and got filament feeding again.', 'IMG_7420.jpeg', 'Installed replacement extruder assembly'],
    ['Repaired · July 6', 'The gear mismatch', 'My stepper had a press-fit gear, rather than the removable screw-mounted variant. The first replacement kit did not match. I reordered the kit and used adhesive foam under the gear to help the gears mesh.', 'IMG_7434.jpeg', 'Stepper motor with the press-fit gear'],
    ['Printing · July 6', 'From failed prints to Benchy', 'With the extruder working, I spent the evening tuning print settings. The next day produced a calibration cube and a Benchy: the first successful test prints of the restoration.', 'IMG_7446.jpeg', 'The first Benchy test print'],
    ['Repair started · July 15', 'In hot water with my hotend', 'Thin, spaghetti-like prints led me to a clogged nozzle. Leaked plastic had locked it in place, and after removing it I found the socket completely stripped. I took out the old hotend and started replacing it with a spare. Automatic bed leveling and a Raspberry Pi print server are still planned for winter.', null, '']
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
  document.querySelector('.printer-explorer').addEventListener('click', event => {
    const button = event.target.closest('[data-part]');
    if (button) select(Number(button.dataset.part));
  });
  select(0);
})();
