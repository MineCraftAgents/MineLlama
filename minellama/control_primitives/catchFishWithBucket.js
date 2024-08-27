async function catchFishWithBucket(bot) {
  // バケツを装備
  const bucket = bot.inventory.findInventoryItem(mcData.itemsByName['bucket'].id);
  if (!bucket) {
      bot.chat("I don't have a bucket.");
      return;
  }
  await bot.equip(bucket, 'hand');

  // 魚を探す
  const fish = bot.nearestEntity(entity => {
      return entity.name === 'cod' || entity.name === 'salmon' || entity.name === 'tropical_fish' || entity.name === 'pufferfish';
  });

  if (!fish) {
      bot.chat("No fish found nearby.");
      return;
  }

  // 魚に近づく
  await bot.pathfinder.goto(new GoalBlock(fish.position.x, fish.position.y, fish.position.z));

  // 魚をすくう
  try {
      await bot.activateEntity(fish);
      bot.chat("Got the fish with the bucket!");
  } catch (err) {
      bot.chat(`Failed to catch the fish: ${err.message}`);
  }
}
