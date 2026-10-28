import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  Card,
  Text,
  Badge,
  Stack,
  Flex,
  ActionIcon,
  Group
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconHeart,
  IconHeartFilled,
  IconClock
} from '@tabler/icons-react';

import type { RecipeSummary } from '../types/recipe';
import { toggleLikeRecipe } from '../api/recipes';
import { formatTime } from '../utils/format';

interface Props {
  recipe: RecipeSummary;
  isLoggedIn: boolean;
  onLikeToggled?: () => void;
}

export const RecipeCard = ({ recipe, isLoggedIn, onLikeToggled }: Props) => {
  const [liked, setLiked] = useState(recipe.is_liked);
  const [likeCount, setLikeCount] = useState(recipe.like_count);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setLiked(recipe.is_liked);
    setLikeCount(recipe.like_count);
  }, [recipe.is_liked, recipe.like_count]);

  const handleLike = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (!isLoggedIn) {
      navigate('/login');
      return;
    }

    if (loading) {
      return;
    }

    const previousLiked = liked;
    const previousCount = likeCount;

    setLiked(!previousLiked);
    setLikeCount(previousLiked ? Math.max(0, previousCount - 1) : previousCount + 1);
    setLoading(true);

    try {
      const result = await toggleLikeRecipe(recipe.id);
      setLiked(result.liked);
      onLikeToggled?.();
    } catch {
      setLiked(previousLiked);
      setLikeCount(previousCount);
      notifications.show({
        title: 'Error',
        message: 'Failed to update favorite status. Please try again.',
        color: 'red'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      withBorder
      shadow='sm'
      radius='lg'
      p='lg'
      bg='teal.1'
      h='100%'
      onClick={() => navigate(`/recipes/${recipe.id}`)}
      style={{ cursor: 'pointer', transition: 'transform 150ms ease' }}
    >
      <Flex direction='column' justify='space-between' h='100%'>
        <Stack gap='xs'>
          <Text fw={700} size='md' c='teal.9' lineClamp={3}>
            {recipe.name}
          </Text>

          <Flex align='center' justify='space-between' gap='xs' wrap='wrap'>
            <Group gap='sm' align='center'>
              {recipe.minutes && (
                <Group gap={4} align='center'>
                  <IconClock size={15} stroke={1.5} color='gray' />
                  <Text size='xs' c='dimmed'>
                    {formatTime(recipe.minutes)}
                  </Text>
                </Group>
              )}

              <Group
                gap={3}
                align='center'
                onClick={handleLike}
                style={{ cursor: 'pointer' }}
              >
                <ActionIcon
                  variant='transparent'
                  color={liked ? 'red.7' : 'gray.6'}
                  size='xs'
                  aria-label={liked ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {liked ? (
                    <IconHeartFilled size={16} />
                  ) : (
                    <IconHeart size={16} stroke={1.7} />
                  )}
                </ActionIcon>
                <Text size='xs' fw={600} c={liked ? 'red.7' : 'dimmed'}>
                  {likeCount}
                </Text>
              </Group>
            </Group>

            {recipe.similarity != null && (
              <Badge
                color='teal'
                variant='light'
                size='sm'
                flex='0 0 auto'
              >
                {(recipe.similarity * 100).toFixed(1)}% match
              </Badge>
            )}
          </Flex>

          <Text size='sm' c='gray.7' lineClamp={3}>
            {recipe.description || 'No description provided.'}
          </Text>
        </Stack>
      </Flex>
    </Card>
  );
};