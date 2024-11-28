async function moveToGroundLevel(bot) {
  const woodLogNames = ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log"];

  // Find a wood log block
  const woodLogBlock = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
    return bot.findBlock({
      matching: block => woodLogNames.includes(block.name),
      maxDistance: 32
    });
  });
  if (!woodLogBlock) {
    bot.chat("Could not find a wood log to find ground.");
    return;
  }
  
  bot.chat("Moving to ground...");
  await bot.pathfinder.goto(new GoalLookAtBlock(woodLogBlock.position, bot.world));
}
