(() => {
  "use strict";

  const projectRoot = document.querySelector("[data-summer-projects]");
  const projectNav = document.querySelector("[data-summer-project-nav]");

  const formatDate = (dateString) => {
    const date = new Date(`${dateString}T12:00:00`);
    if (Number.isNaN(date.getTime())) {
      return dateString;
    }
    return new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(date);
  };

  const appendParagraphs = (parent, body) => {
    body
      .split(/\n\s*\n/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean)
      .forEach((paragraph) => {
        const element = document.createElement("p");
        element.textContent = paragraph;
        parent.append(element);
      });
  };

  const renderImage = (image) => {
    const figure = document.createElement("figure");
    figure.className = "summer-project-photo-card";

    const element = document.createElement("img");
    element.src = `../${image.src}`;
    element.alt = image.alt || "";
    element.className = "project-image summer-project-image-sm";
    element.loading = "lazy";
    figure.append(element);

    if (image.caption) {
      const caption = document.createElement("figcaption");
      caption.textContent = image.caption;
      figure.append(caption);
    }
    return figure;
  };

  const appendGallery = (parent, images) => {
    if (!Array.isArray(images) || images.length === 0) {
      return;
    }
    const gallery = document.createElement("div");
    gallery.className = "summer-project-gallery summer-project-gallery-featured";
    images.forEach((image) => gallery.append(renderImage(image)));
    parent.append(gallery);
  };

  const renderProject = (project) => {
    const section = document.createElement("section");
    section.id = project.id;
    section.className = "summer-project-section summer-added-project";

    const kicker = document.createElement("p");
    kicker.className = "project-kicker";
    kicker.textContent = `New project · ${formatDate(project.date)}`;

    const heading = document.createElement("h2");
    heading.textContent = project.title;

    section.append(kicker, heading);
    appendParagraphs(section, project.body);
    appendGallery(section, project.images);

    const updates = document.createElement("div");
    updates.className = "summer-live-updates";
    updates.dataset.summerUpdates = project.id;
    section.append(updates);
    return section;
  };

  const renderUpdate = (update) => {
    const article = document.createElement("article");
    article.className = "summer-log-entry";

    const meta = document.createElement("p");
    meta.className = "project-kicker summer-log-date";
    meta.textContent = formatDate(update.date);

    const heading = document.createElement("h3");
    heading.textContent = update.title;

    article.append(meta, heading);
    appendParagraphs(article, update.body);
    appendGallery(article, update.images);
    return article;
  };

  fetch("../data/summer-updates.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Could not load summer content (${response.status})`);
      }
      return response.json();
    })
    .then((data) => {
      const projects = Array.isArray(data.projects) ? data.projects : [];
      projects
        .slice()
        .reverse()
        .forEach((project) => {
          if (projectRoot) {
            projectRoot.append(renderProject(project));
          }
          if (projectNav) {
            const link = document.createElement("a");
            link.href = `#${project.id}`;
            link.textContent = project.title;
            projectNav.append(link);
          }
        });

      const containers = new Map(
        Array.from(document.querySelectorAll("[data-summer-updates]")).map((element) => [
          element.dataset.summerUpdates,
          element,
        ]),
      );
      const updates = Array.isArray(data.updates) ? data.updates : [];
      updates
        .slice()
        .sort((a, b) => a.date.localeCompare(b.date))
        .forEach((update) => {
          const container = containers.get(update.project);
          if (container) {
            container.append(renderUpdate(update));
          }
        });
    })
    .catch((error) => {
      console.error("Summer content:", error);
    });
})();
