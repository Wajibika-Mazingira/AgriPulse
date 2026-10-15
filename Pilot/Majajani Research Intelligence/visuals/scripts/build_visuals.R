#!/usr/bin/env Rscript
# Base-R companion figures from the cited CSV tables; no CRAN packages required.
# Run from any directory: Rscript scripts/build_visuals.R

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_file <- normalizePath(sub("^--file=", "", file_arg[[1]]))
root <- normalizePath(file.path(dirname(script_file), ".."))
data_dir <- file.path(root, "data")
figure_dir <- file.path(root, "figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

elephants <- read.csv(file.path(data_dir, "elephant_estimates.csv"), stringsAsFactors = FALSE)
displacement <- read.csv(file.path(data_dir, "displacement_evidence.csv"), stringsAsFactors = FALSE)
sites <- read.csv(file.path(data_dir, "sites.csv"), stringsAsFactors = FALSE)
nodes <- read.csv(file.path(data_dir, "network_nodes.csv"), stringsAsFactors = FALSE)
edges <- read.csv(file.path(data_dir, "network_edges.csv"), stringsAsFactors = FALSE)

# Elephant estimates: Arabuko-Sokoke uncertainty and separate regional context.
png(file.path(figure_dir, "elephant_estimates_R.png"), width = 1800, height = 900, res = 160)
par(mfrow = c(1, 2), mar = c(5, 9, 4, 2), oma = c(2, 0, 1, 0), bg = "white")
forest <- elephants[elephants$population == "Arabuko-Sokoke Forest", ]
plot(forest$estimate, 1, xlim = c(0, 350), ylim = c(0.5, 1.5), yaxt = "n", pch = 19,
     col = "#227C70", cex = 1.5, xlab = "Elephants (95% CI)", ylab = "",
     main = "Kilifi forest estimate", bty = "n")
axis(2, at = 1, labels = "Arabuko-Sokoke", las = 1)
segments(forest$lower_ci, 1, forest$upper_ci, 1, col = "#227C70", lwd = 2)
segments(forest$lower_ci, 0.94, forest$lower_ci, 1.06, col = "#227C70", lwd = 2)
segments(forest$upper_ci, 0.94, forest$upper_ci, 1.06, col = "#227C70", lwd = 2)
grid(nx = NA, ny = NULL, col = "#E3E8EB")
text(12, 0.67, "2017 dung count: 215; 95% CI: 145–318", adj = 0, cex = 0.85)

context <- elephants[elephants$population %in% c("Shimba Hills", "Tsavo ecosystem"), ]
bp_context <- barplot(context$estimate, names.arg = context$population, horiz = TRUE, las = 1,
        col = c("#8064A2", "#227C70"), xlim = c(0, 20500), xlab = "Elephants (separate ecosystem estimates)",
        main = "Regional context — not Kilifi counts", border = NA, axes = FALSE)
axis(1, at = seq(0, 20000, by = 5000), col = "#66737C", col.axis = "#33414A")
text(context$estimate + 300, bp_context,
     labels = paste(format(context$estimate, big.mark = ","), context$estimate_year, sep = " · "),
     pos = 4, cex = 0.66, xpd = TRUE)
grid(nx = NULL, ny = NA, col = "#E3E8EB")
mtext("Source: KWS/WRTI (2023), reproducing Waweru et al. (2021). Different methods and dates; not a trend series.",
      side = 1, outer = TRUE, line = 0.5, cex = 0.72, col = "#44515A")
dev.off()

# Resettlement claims are shown in separate panels because their units differ.
png(file.path(figure_dir, "displacement_evidence_R.png"), width = 1500, height = 1200, res = 160)
par(mfrow = c(2, 2), mar = c(5, 6, 4, 1), oma = c(2, 0, 1, 0), bg = "white")
counts <- displacement[displacement$unit %in% c("households", "people"), ]
bp <- barplot(counts$value, names.arg = c("Households\n(Maumba)", "People\n(Kwale)"),
        col = c("#C65D3A", "#D98465"), ylab = "Source-reported count",
        main = "Different units and source bases", border = NA, ylim = c(0, 3600))
text(bp, counts$value + 100, c("480 households", ">3,000 people"), cex = 0.75)
mtext("Not an audited total", side = 1, line = 3, cex = 0.75)

disputes <- displacement[displacement$unit == "disputes", ]
barplot(disputes$value, names.arg = c("Over 100\nreported", "91 alleged\nno compensation"),
        col = c("#C65D3A", "#D98465"), ylab = "Reported case count",
        main = "Community-reported disputes (2016)", border = NA, ylim = c(0, 125))
mtext("Not current case status", side = 1, line = 3, cex = 0.75)

acreage <- displacement[displacement$unit == "acres", ]
barplot(acreage$value, names.arg = c("Claimed", "Reportedly\ncompensated"),
        col = c("#65717C", "#D08B22"), ylab = "Acres",
        main = "One Nguluku farmer’s account (2024)", border = NA, ylim = c(0, 38))
mtext("Individual testimony; not adjudicated", side = 1, line = 3, cex = 0.7)

money <- displacement$value[displacement$unit == "KES"]
plot.new()
text(0.5, 0.78, "Reported payment in the same account", cex = 1.0, font = 2)
text(0.5, 0.52, paste("KES", format(money, big.mark = ",")), cex = 1.5, col = "#D08B22", font = 2)
text(0.5, 0.26, "Not a compensation tariff", cex = 0.9)
mtext("Sources: Global Press Journal (2016); Abuya (2016); Dialogue Earth (2024). Company responses are noted in the paper.",
      side = 1, outer = TRUE, line = 0.5, cex = 0.65, col = "#44515A")
dev.off()

# Approximate reference map; exact estate, mine and Kaya boundaries are absent.
mapped <- sites[!is.na(sites$latitude) & !is.na(sites$longitude), ]
colors <- c("#227C70", "#C65D3A", "#C65D3A", "#D08B22", "#227C70", "#8064A2", "#227C70")
symbols <- c(21, 22, 24, 23, 21, 22, 8)
png(file.path(figure_dir, "regional_sites_map_R.png"), width = 1500, height = 1200, res = 160)
par(mar = c(7, 5, 4, 1), bg = "#EAF3F5")
plot(NA, xlim = c(38.65, 40.18), ylim = c(-4.62, -2.68), asp = NA,
     xlab = "Longitude (°E)", ylab = "Latitude (°S; negative degrees)",
     main = "Kilifi elephant locations and separate Kwale titanium project", bty = "n")
abline(h = pretty(c(-4.62, -2.68)), v = pretty(c(38.65, 40.18)), col = "white", lwd = 1.1)
lines(c(38.8, 39.855476), c(-3.2, -3.349628), lty = 2, lwd = 2, col = "#227C70")
text(39.25, -3.11, "Arabuko–Tsavo linkage (schematic)", cex = 0.72, col = "#227C70")
for (i in seq_len(nrow(mapped))) {
  points(mapped$longitude[i], mapped$latitude[i], pch = symbols[i], bg = colors[i], col = "white", cex = 1.5)
  label <- if (mapped$site_id[i] == "BASEMINE") "Kwale titanium mine\n(approx.)" else mapped$name[i]
  dx <- if (mapped$site_id[i] == "BASEMINE") -0.29 else 0.025
  dy <- if (mapped$site_id[i] == "BASEMINE") -0.08 else 0.025
  if (mapped$site_id[i] == "SHIMBA") { dx <- -0.30; dy <- -0.04 }
  if (mapped$site_id[i] == "KAYAKINONDO") { dx <- 0.04; dy <- 0.045 }
  if (mapped$site_id[i] == "TSAVOEAST") { dx <- 0.06; dy <- 0.02; label <- "Tsavo East" }
  text(mapped$longitude[i] + dx, mapped$latitude[i] + dy, label, cex = 0.7, adj = 0)
}
dev.off()

# Evidence graph using the explicitly sourced, non-causal edge table.
position <- data.frame(x = nodes$plot_x, y = nodes$plot_y, row.names = nodes$node_id)
png(file.path(figure_dir, "evidence_network_R.png"), width = 1800, height = 1100, res = 160)
par(mar = c(1, 1, 4, 1), bg = "white")
plot(NA, xlim = c(-0.8, 7.3), ylim = c(-1.7, 2.7), axes = FALSE, xlab = "", ylab = "",
     main = "Evidence-linked actors, places and processes", bty = "n")
for (i in seq_len(nrow(edges))) {
  a <- position[edges$from_id[i], ]
  b <- position[edges$to_id[i], ]
  reported <- grepl("allegation|reported|question", edges$evidence_class[i], ignore.case = TRUE)
  arrows(a$x, a$y, b$x, b$y, length = 0.08, lwd = 1.2,
         col = if (reported) "#C65D3A" else "#6B7780", lty = if (reported) 2 else 1)
}
node_cols <- c("#376996", "#376996", "#8064A2", "#4B83A6", "#C65D3A", "#227C70", "#227C70", "#D98465", "#D08B22", "#65717C", "#C65D3A", "#376996", "#8064A2")
points(nodes$plot_x, nodes$plot_y, pch = 21, bg = node_cols, col = "white", cex = 4.4, lwd = 1.5)
text(nodes$plot_x, nodes$plot_y, labels = nodes$graph_label, col = "white", cex = 0.66, font = 2)
mtext("Node IDs resolve to full names in network_nodes.csv. Edges are evidence-linked, not causal findings.", side = 1, line = -1.2, cex = 0.75, col = "#44515A")
dev.off()

cat("Base-R figures written to", figure_dir, "\n")
