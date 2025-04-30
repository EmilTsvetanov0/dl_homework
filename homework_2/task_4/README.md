1. Как отличаются генерации с temperature = [1.0, 0.5] и top_p = [0.9, 0.15]?

        При большом top_p и результат становится почти таким же, что и без его влияния, оставляя почти что только эффект вызванный температурой
        При маленьком top_p результат почти такой же, что и при любой маленькой температуре почти убирая эффект температуры
        Это подтверждает результат: при temperature=1.0 и top_p=0.15 первая часть текста вышла почти такой же, что и при жадном выборе токенов

2. Помог ли nucleus sampling исправить какие-то проблемы, которые были при простом сэмплировании с температурой?

        Есть проблема, которую потенциально может решить подбор оптимального top_p:
        Отсекая самые маловероятные токены с помощью выбора top_p поменьше (но не слишком), мы
        грубо говоря держим модель в узде, чтобы она не генерировала прям совсем бред, однако сохраняем креативность
        таким образом, что среди оставшихся токенов всё равно рандом имеет место быть
        То есть мы делаем так, чтобы креативность модели (заданная температурой) не выходила за адекватные рамки (которые задаются с помощью top_p)

3. Результат

=== Hedgehog story (temp=1.0, top_p=0.9) ===

Once upon a time, in a small, cozy town nestled among the rolling hills, there lived a little hedgehog named Sonic. Sonic was a very small creature, with a soft red fur that shimmered under the sun, and a playful heart that could entertain his friends with his antics.

One crisp autumn morning, Sonic woke up to the sound of leaves crunching underfoot. He stretched and stretched, eager to take the first step out of his nest. After several excited minutes of piling up leaves and crunching them into tiny piles, Sonic made his way outside.

The sun was shining, and the birds were singing in the trees. In the distance, a golden bear’s family gathered around a fire pit, playing frisbee and talking to each other. Sonic felt a bit nervous, but he was curious about the big, furry creatures that lived around here.

As he walked closer to the family, Sonic couldn’t help but notice that they had large skunks and bears. These were not friendly, but they didn’t seem to scare Sonic off. Sonic felt curious, but also a bit shy.

The bear gave Sonic a hearty, beaming hug, and then they headed off into the forest to play. Sonic watched, fascinated, as the bears, skunks, and even a few squirrels darted around. He could see the sounds of playful screeching and clicking feathers.

As the sun began to set, the bear’s family gathered around a campfire, cooking roast beef and catching sparks. Sonic couldn’t wait to venture out and explore, hoping to join in the fun and discover the wild life that lived here.

With a big hug from the bear and a loud, enthusiastic giggle, Sonic made his way back to his nest. He climbed into a cozy, raised bed of leaves and a soft blanket, ready to take on the world outside his small, warm home.


=== JSON (temp=1.0, top_p=0.9) ===

{"contractor": "Mike", "sum": 105, "currency": "rub"}

=== Hedgehog story (temp=1.0, top_p=0.15) ===

Once upon a time, in a small, cozy village nestled in the heart of the forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with magical items. As he opened the chest, he was amazed to see that the items were not just ordinary, but enchanted. Sonic was thrilled to find that he could use the items to help others in need.

From that day on, Sonic became a hero in the village. He used his magical powers to help people in need, and soon, the village was filled with people who were grateful for the help they received from Sonic.

Sonic's story became a legend, and people from all over the village would tell stories about him. Sonic's adventures and his magic helped to bring joy and hope to the people of the village, and he was loved and respected by all who knew him.

And so, Sonic continued to be a tiny hedgehog, always on the lookout for new adventures and helping others in need.


=== JSON (temp=1.0, top_p=0.15) ===

{"contractor": "Mike", "sum": 105, "currency": "rubles"}

=== Hedgehog story (temp=0.5, top_p=0.9) ===

Once upon a time, in a small, hidden forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a mysterious cave entrance.

As Sonic ventured deeper into the cave, he discovered a hidden chamber filled with strange, glowing crystals. The crystals were said to have the power to grant wishes, but only if one could find the correct key.

Sonic was determined to find the key and use it to grant his wish. He searched the cave for hours, but found nothing. Then, he stumbled upon a group of friendly, friendly animals who were helping him. They showed him the way to the key and explained that it was hidden in a nearby tree.

With a grateful heart, Sonic climbed up the tree and found the key. He used it to unlock the cave door and entered the chamber filled with glowing crystals. As he looked around, he realized that the crystals were not just for fun, but for something much more important.

Sonic found the key and used it to unlock a hidden door. Inside, he found a treasure chest filled with gold coins, jewels, and other valuable items. Sonic was overjoyed and couldn't wait to share his newfound wealth with his friends.

From that day on, Sonic became known as the treasure hunter of the forest. He spent his days exploring the world and discovering new treasures, and his adventures were always filled with excitement and adventure.

=== JSON (temp=0.5, top_p=0.9) ===

{"contractor": "Mike", "sum": 105, "currency": "rubles"}

=== Hedgehog story (temp=0.5, top_p=0.15) ===

Once upon a time, in a small, cozy village nestled in the heart of the forest, there lived a tiny hedgehog named Sonic. Sonic was a curious and adventurous creature, always eager to explore the world around him. One day, while wandering through the forest, Sonic stumbled upon a hidden cave.

Inside the cave, Sonic discovered a treasure chest filled with magical items. As he opened the chest, he was amazed to see that the items were not just ordinary, but enchanted. Sonic was thrilled to find that he could use the items to help others in need.

From that day on, Sonic became a hero in the village. He used his magical powers to help people in need, and soon, the village was filled with people who were grateful for the help they received from Sonic.

Sonic's story became a legend, and people from all over the village would tell stories about him. Sonic's adventures and his magic helped to bring joy and hope to the people of the village, and he was loved and respected by all who knew him.

And so, Sonic continued to be a tiny hedgehog, always on the lookout for new adventures and helping others in need.

=== JSON (temp=0.5, top_p=0.15) ===

{"contractor": "Mike", "sum": 105, "currency": "rubles"}