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
import type { RecipeSummary } from '../types/recipe';
import { toggleLikeRecipe } from '../api/recipes';

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
          <Flex justify='space-between' align='flex-start' gap='xs'>
            <Text fw={700} size='md' c='teal.9' lineClamp={2} flex={1}>
              {recipe.name}
            </Text>

            <Group gap={6} wrap='nowrap' align='center'>
              {recipe.similarity != null && (
                <Badge
                  color='teal'
                  variant='light'
                  size='md'
                  flex='0 0 auto'
                >
                  {(recipe.similarity * 100).toFixed(1)}% match
                </Badge>
              )}
              <ActionIcon
                variant={liked ? 'filled' : 'subtle'}
                color='red'
                size='lg'
                radius='xl'
                loading={loading}
                onClick={handleLike}
                aria-label={liked ? 'Remove from favorites' : 'Add to favorites'}
              >
                {liked ? '❤️' : '🤍'}
              </ActionIcon>
            </Group>
          </Flex>

          <Flex align='center' gap='sm'>
            {recipe.minutes && (
              <Text size='xs' c='dimmed'>
                Prep time: {recipe.minutes} mins
              </Text>
            )}
            {recipe.minutes && (
              <Text size='xs' c='dimmed'>•</Text>
            )}
            <Text size='xs' c='dimmed'>
              ❤️ {likeCount} {likeCount === 1 ? 'like' : 'likes'}
            </Text>
          </Flex>

          <Text size='sm' c='gray.7' lineClamp={4}>
            {recipe.description || 'No description provided.'}
          </Text>
        </Stack>
      </Flex>
    </Card>
  );
};