""Initial migration

Revision ID: initial
Revises: 
Create Date: 2023-10-15 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum types
    user_role = postgresql.ENUM(
        'user', 'manager', 'admin', 'super_admin',
        name='userrole',
        create_type=True
    )
    user_status = postgresql.ENUM(
        'pending', 'active', 'suspended', 'deleted',
        name='userstatus',
        create_type=True
    )
    post_status = postgresql.ENUM(
        'draft', 'scheduled', 'publishing', 'published', 'failed', 'canceled',
        name='poststatus',
        create_type=True
    )
    post_content_type = postgresql.ENUM(
        'text', 'image', 'video', 'carousel', 'story', 'reel', 'link', 'poll',
        name='postcontenttype',
        create_type=True
    )
    social_platform = postgresql.ENUM(
        'facebook', 'instagram', 'twitter', 'linkedin', 'pinterest', 'tiktok', 'youtube', 'google_my_business', 'snapchat',
        name='socialplatform',
        create_type=True
    )
    social_account_status = postgresql.ENUM(
        'pending', 'connected', 'error', 'disconnected', 'expired',
        name='socialaccountstatus',
        create_type=True
    )
    media_type = postgresql.ENUM(
        'image', 'video', 'gif', 'audio', 'document', 'archive', 'other',
        name='mediatype',
        create_type=True
    )
    media_status = postgresql.ENUM(
        'uploading', 'processing', 'ready', 'error', 'deleted',
        name='mediastatus',
        create_type=True
    )
    media_variant_type = postgresql.ENUM(
        'original', 'thumbnail', 'small', 'medium', 'large', 'hd', 'story', 'profile',
        name='mediavarianttype',
        create_type=True
    )
    
    # Create all enum types first
    op.execute('COMMIT')  # End any existing transaction
    for enum_type in [user_role, user_status, post_status, post_content_type, 
                     social_platform, social_account_status, media_type, 
                     media_status, media_variant_type]:
        enum_type.create(op.get_bind())

    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(length=100), nullable=True, unique=True),
        sa.Column('verification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('user', 'manager', 'admin', 'super_admin', name='userrole'), nullable=False, server_default='user'),
        sa.Column('status', sa.Enum('pending', 'active', 'suspended', 'deleted', name='userstatus'), nullable=False, server_default='pending'),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create the rest of the tables...
    # (I'll continue with the remaining tables in the next response to avoid timeout)
    
    # Create indexes
    op.create_index('ix_users_status', 'users', ['status'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_status', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    op.execute("DROP TYPE IF EXISTS userstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS poststatus CASCADE")
    op.execute("DROP TYPE IF EXISTS postcontenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS socialplatform CASCADE")
    op.execute("DROP TYPE IF EXISTS socialaccountstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS mediatype CASCADE")
    op.execute("DROP TYPE IF EXISTS mediastatus CASCADE")
    op.execute("DROP TYPE IF EXISTS mediavarianttype CASCADE")
